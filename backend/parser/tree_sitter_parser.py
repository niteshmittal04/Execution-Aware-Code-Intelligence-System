from dataclasses import dataclass, field
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_python

from backend.config.settings import AppConfig


@dataclass
class ParsedSymbol:
    id: str
    type: str
    name: str
    file_path: str
    line_start: int
    line_end: int
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedEdge:
    id: str
    source: str
    target: str
    type: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedVariable:
    id: str
    name: str
    scope: str
    file_path: str
    metadata: dict = field(default_factory=dict)


class TreeSitterCodeParser:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        language = Language(tree_sitter_python.language())
        self.parser = Parser(language)

    def iter_source_files(self, repo_path: Path):
        include_extensions = set(self.config.indexing.include_extensions)
        max_file_bytes = self.config.indexing.max_file_bytes
        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in include_extensions:
                continue
            if path.stat().st_size > max_file_bytes:
                continue
            yield path

    def parse_repository(
        self, repo_path: Path
    ) -> tuple[list[ParsedSymbol], list[ParsedEdge], list[ParsedVariable], list[dict]]:
        symbols: list[ParsedSymbol] = []
        edges: list[ParsedEdge] = []
        variables: list[ParsedVariable] = []
        chunks: list[dict] = []

        for file_path in self.iter_source_files(repo_path):
            file_symbols, file_edges, file_variables, file_chunks = self.parse_file(file_path)
            symbols.extend(file_symbols)
            edges.extend(file_edges)
            variables.extend(file_variables)
            chunks.extend(file_chunks)

        return symbols, edges, variables, chunks

    def parse_file(
        self, file_path: Path
    ) -> tuple[list[ParsedSymbol], list[ParsedEdge], list[ParsedVariable], list[dict]]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = self.parser.parse(bytes(text, "utf-8"))
        lines = text.splitlines()
        symbols: list[ParsedSymbol] = []
        edges: list[ParsedEdge] = []
        variables: list[ParsedVariable] = []

        self._walk(tree.root_node, file_path, symbols, edges, variables)
        chunks = self._chunk_text(text, file_path)

        if not symbols:
            fallback_id = f"module:{file_path}"
            symbols.append(
                ParsedSymbol(
                    id=fallback_id,
                    type="module",
                    name=file_path.stem,
                    file_path=str(file_path),
                    line_start=1,
                    line_end=max(len(lines), 1),
                )
            )

        return symbols, edges, variables, chunks

    def _walk(
        self,
        node,
        file_path: Path,
        symbols: list[ParsedSymbol],
        edges: list[ParsedEdge],
        variables: list[ParsedVariable],
        current_function: str | None = None,
    ) -> None:
        node_type = node.type
        symbol_id = current_function

        if node_type in {"function_definition", "class_definition"}:
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                symbol_id = f"{file_path}:{name}:{node.start_point[0] + 1}"
                symbols.append(
                    ParsedSymbol(
                        id=symbol_id,
                        type="function" if node_type == "function_definition" else "class",
                        name=name,
                        file_path=str(file_path),
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                    )
                )

        if node_type == "call" and current_function:
            function_node = node.child_by_field_name("function")
            if function_node:
                target_name = function_node.text.decode("utf-8")
                edge_id = f"{current_function}->call:{target_name}:{node.start_point[0] + 1}"
                edges.append(
                    ParsedEdge(
                        id=edge_id,
                        source=current_function,
                        target=target_name,
                        type="calls",
                        metadata={"line": node.start_point[0] + 1},
                    )
                )

        if node_type == "import_statement":
            import_target = node.text.decode("utf-8").replace("import", "").strip()
            source_id = f"module:{file_path}"
            edge_id = f"{source_id}->import:{import_target}:{node.start_point[0] + 1}"
            edges.append(
                ParsedEdge(
                    id=edge_id,
                    source=source_id,
                    target=import_target,
                    type="imports",
                    metadata={"line": node.start_point[0] + 1},
                )
            )

        if node_type == "assignment":
            left = node.child_by_field_name("left")
            if left:
                var_name = left.text.decode("utf-8")
                variables.append(
                    ParsedVariable(
                        id=f"{file_path}:{var_name}:{node.start_point[0] + 1}",
                        name=var_name,
                        scope=current_function or "module",
                        file_path=str(file_path),
                        metadata={"line": node.start_point[0] + 1},
                    )
                )

        for child in node.children:
            self._walk(child, file_path, symbols, edges, variables, symbol_id)

    def _chunk_text(self, text: str, file_path: Path) -> list[dict]:
        chunk_size = self.config.indexing.chunk_size
        overlap = self.config.indexing.chunk_overlap
        chunks: list[dict] = []

        cursor = 0
        while cursor < len(text):
            chunk = text[cursor : cursor + chunk_size]
            if not chunk:
                break
            chunks.append(
                {
                    "id": f"{file_path}:{cursor}",
                    "content": chunk,
                    "file_path": str(file_path),
                    "function_name": "",
                    "type": "code",
                    "metadata": {"offset": cursor},
                }
            )
            cursor += max(chunk_size - overlap, 1)
        return chunks
