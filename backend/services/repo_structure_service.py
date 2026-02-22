import ast
from pathlib import Path

from backend.parser.tree_sitter_parser import TreeSitterCodeParser
from backend.services.repo_session_manager import RepoSessionManager


class _PythonStructureVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.classes: list[dict] = []
        self.functions: list[dict] = []
        self._class_depth = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        class_node = {
            "type": "class",
            "name": node.name,
            "line": getattr(node, "lineno", None),
            "children": [],
        }
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                class_node["children"].append(
                    {
                        "type": "function",
                        "name": child.name,
                        "line": getattr(child, "lineno", None),
                    }
                )
        self.classes.append(class_node)
        self._class_depth += 1
        for child in node.body:
            if isinstance(child, ast.ClassDef):
                self.visit(child)
        self._class_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        if self._class_depth > 0:
            return
        self.functions.append(
            {
                "type": "function",
                "name": node.name,
                "line": getattr(node, "lineno", None),
            }
        )

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        if self._class_depth > 0:
            return
        self.functions.append(
            {
                "type": "function",
                "name": node.name,
                "line": getattr(node, "lineno", None),
            }
        )


class RepoStructureService:
    def __init__(self, parser: TreeSitterCodeParser, session_manager: RepoSessionManager) -> None:
        self.parser = parser
        self.session_manager = session_manager

    def extract_repo_structure(
        self,
        repo_path: Path,
        session_id: str,
        force_refresh: bool = False,
    ) -> dict:
        if not force_refresh:
            cached = self.session_manager.get_cached_structure(session_id)
            if cached:
                return cached

        root = {
            "type": "repo",
            "name": repo_path.name,
            "path": str(repo_path),
            "children": [],
        }

        dirs_by_relpath: dict[str, dict] = {".": root}

        for repo_file in self._iter_repo_files(repo_path):
            relative_path = repo_file.relative_to(repo_path)
            parent = relative_path.parent
            parent_node = self._ensure_directories(dirs_by_relpath, root, parent)
            file_node = self._build_file_node(repo_path, repo_file)
            parent_node["children"].append(file_node)

        self._sort_tree(root)
        self.session_manager.store_structure(session_id, root)
        return root

    def _iter_repo_files(self, repo_path: Path):
        excluded_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
        }

        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue

            relative = path.relative_to(repo_path)
            if any(part in excluded_dirs for part in relative.parts):
                continue

            yield path

    def _ensure_directories(self, dirs_by_relpath: dict[str, dict], root: dict, parent: Path) -> dict:
        if str(parent) in {"", "."}:
            return root

        current = Path(".")
        current_node = root
        for part in parent.parts:
            current = current / part
            key = str(current)
            existing = dirs_by_relpath.get(key)
            if existing is None:
                existing = {
                    "type": "directory",
                    "name": part,
                    "path": key,
                    "children": [],
                }
                current_node["children"].append(existing)
                dirs_by_relpath[key] = existing
            current_node = existing
        return current_node

    def _build_file_node(self, repo_path: Path, source_file: Path) -> dict:
        relative = source_file.relative_to(repo_path)
        file_node = {
            "type": "file",
            "name": source_file.name,
            "path": str(relative),
            "children": [],
        }

        if source_file.suffix != ".py":
            return file_node

        module_node = {
            "type": "module",
            "name": source_file.stem,
            "path": str(relative),
            "children": [],
        }

        try:
            source = source_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            visitor = _PythonStructureVisitor()
            visitor.visit(tree)

            class_names = {entry["name"] for entry in visitor.classes}
            module_node["children"].extend(visitor.classes)
            module_node["children"].extend(
                entry for entry in visitor.functions if entry["name"] not in class_names
            )
        except Exception:
            pass

        file_node["children"].append(module_node)
        return file_node

    def _sort_tree(self, node: dict) -> None:
        children = node.get("children")
        if not isinstance(children, list):
            return

        type_order = {
            "directory": 0,
            "file": 1,
            "module": 2,
            "class": 3,
            "function": 4,
        }
        children.sort(key=lambda item: (type_order.get(item.get("type"), 10), item.get("name", "")))
        for child in children:
            self._sort_tree(child)
