import json
import sqlite3
from pathlib import Path

from backend.config.settings import AppConfig
from backend.parser.tree_sitter_parser import ParsedEdge, ParsedSymbol, ParsedVariable


class SqliteGraphStore:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._connections: dict[str, sqlite3.Connection] = {}

    def _session_db_path(self, session_id: str) -> Path:
        return Path("./data/graph_storage") / session_id / "graph.db"

    def _get_connection(self, session_id: str) -> sqlite3.Connection:
        existing = self._connections.get(session_id)
        if existing is not None:
            return existing

        db_path = self._session_db_path(session_id)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self._init_schema(conn)
        self._connections[session_id] = conn
        return conn

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT,
                name TEXT,
                file_path TEXT,
                line_start INTEGER,
                line_end INTEGER,
                metadata TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source TEXT,
                target TEXT,
                type TEXT,
                metadata TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS variables (
                id TEXT PRIMARY KEY,
                name TEXT,
                scope TEXT,
                file_path TEXT,
                metadata TEXT
            )
            """
        )
        conn.commit()

    def upsert_graph(
        self,
        session_id: str,
        nodes: list[ParsedSymbol],
        edges: list[ParsedEdge],
        variables: list[ParsedVariable],
    ) -> None:
        conn = self._get_connection(session_id)
        batch_size = self.config.indexing.batch_size
        for start in range(0, len(nodes), batch_size):
            batch = nodes[start : start + batch_size]
            conn.executemany(
                """
                INSERT OR REPLACE INTO nodes (id, type, name, file_path, line_start, line_end, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        item.type,
                        item.name,
                        item.file_path,
                        item.line_start,
                        item.line_end,
                        json.dumps(item.metadata),
                    )
                    for item in batch
                ],
            )
            conn.commit()

        for start in range(0, len(edges), batch_size):
            batch = edges[start : start + batch_size]
            conn.executemany(
                """
                INSERT OR REPLACE INTO edges (id, source, target, type, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        item.source,
                        item.target,
                        item.type,
                        json.dumps(item.metadata),
                    )
                    for item in batch
                ],
            )
            conn.commit()

        for start in range(0, len(variables), batch_size):
            batch = variables[start : start + batch_size]
            conn.executemany(
                """
                INSERT OR REPLACE INTO variables (id, name, scope, file_path, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        item.name,
                        item.scope,
                        item.file_path,
                        json.dumps(item.metadata),
                    )
                    for item in batch
                ],
            )
            conn.commit()

    def get_function_graph(self, session_id: str, function_name: str) -> tuple[list[dict], list[dict]]:
        conn = self._get_connection(session_id)
        depth = self.config.graph.traversal_depth
        page_size = self.config.graph.graph_page_size

        lookup_names = self._candidate_function_names(function_name)
        lowered_names = [item.lower() for item in lookup_names if item]

        seed_rows: list[sqlite3.Row] = []
        if lowered_names:
            placeholders = ",".join(["?"] * len(lowered_names))
            seed_rows = conn.execute(
                f"SELECT * FROM nodes WHERE LOWER(name) IN ({placeholders}) LIMIT ?",
                (*lowered_names, page_size),
            ).fetchall()

        if not seed_rows:
            fallback_term = function_name.strip().lower()
            if fallback_term:
                wildcard = f"%{fallback_term}%"
                seed_rows = conn.execute(
                    """
                    SELECT * FROM nodes
                    WHERE LOWER(id) LIKE ?
                       OR LOWER(file_path) LIKE ?
                       OR LOWER(name) LIKE ?
                    LIMIT ?
                    """,
                    (wildcard, wildcard, wildcard, page_size),
                ).fetchall()

        seen_nodes = {row["id"]: dict(row) for row in seed_rows}
        frontier = [row["id"] for row in seed_rows]
        expanded_node_ids: set[str] = set()
        all_edges: dict[str, dict] = {}

        for _ in range(depth):
            next_seed_ids = [node_id for node_id in frontier if node_id not in expanded_node_ids]
            if not next_seed_ids:
                break
            expanded_node_ids.update(next_seed_ids)

            placeholders = ",".join(["?"] * len(next_seed_ids))
            edge_rows = conn.execute(
                f"""
                SELECT * FROM edges
                WHERE source IN ({placeholders}) OR target IN ({placeholders})
                LIMIT ?
                """,
                (*next_seed_ids, *next_seed_ids, page_size),
            ).fetchall()
            all_edges.update({row["id"]: dict(row) for row in edge_rows})

            connected_node_ids = set()
            for edge in edge_rows:
                connected_node_ids.add(edge["source"])
                connected_node_ids.add(edge["target"])

            if connected_node_ids:
                placeholders = ",".join(["?"] * len(connected_node_ids))
                node_rows = conn.execute(
                    f"SELECT * FROM nodes WHERE id IN ({placeholders}) LIMIT ?",
                    (*connected_node_ids, page_size),
                ).fetchall()
                frontier = []
                for row in node_rows:
                    node_id = row["id"]
                    if node_id not in seen_nodes:
                        seen_nodes[node_id] = dict(row)
                        frontier.append(node_id)
            else:
                frontier = []

        valid_node_ids = set(seen_nodes.keys())
        valid_edges: list[dict] = []
        for edge in all_edges.values():
            if edge["source"] not in valid_node_ids:
                continue
            if edge["target"] not in valid_node_ids:
                seen_nodes[edge["target"]] = {
                    "id": edge["target"],
                    "type": "external",
                    "name": edge["target"],
                    "file_path": "",
                    "line_start": None,
                    "line_end": None,
                    "metadata": "{}",
                }
                valid_node_ids.add(edge["target"])
            valid_edges.append(edge)

        return list(seen_nodes.values()), valid_edges

    def _candidate_function_names(self, function_name: str) -> list[str]:
        normalized = function_name.strip()
        if not normalized:
            return [normalized]

        if normalized.startswith("def "):
            normalized = normalized[4:].strip()

        if normalized.endswith(":"):
            normalized = normalized[:-1].strip()

        if "(" in normalized:
            normalized = normalized.split("(", 1)[0].strip()

        if normalized.endswith(".py"):
            normalized = normalized[:-3].strip()

        candidates = {normalized}
        for separator in ("::", ".", ":", "/", "\\"):
            if separator in normalized:
                tail = normalized.split(separator)[-1].strip()
                if tail:
                    candidates.add(tail)

        if normalized.endswith(".py"):
            candidates.add(normalized[:-3].strip())

        return list(candidates)

    def get_variables_for_scope(self, session_id: str, function_name: str) -> list[dict]:
        conn = self._get_connection(session_id)
        rows = conn.execute(
            "SELECT * FROM variables WHERE scope LIKE ? LIMIT ?",
            (f"%{function_name}%", self.config.graph.graph_page_size),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_graph_stats(self, session_id: str) -> dict:
        conn = self._get_connection(session_id)
        node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        variable_count = conn.execute("SELECT COUNT(*) FROM variables").fetchone()[0]
        return {
            "nodes": int(node_count),
            "edges": int(edge_count),
            "variables": int(variable_count),
        }

    def get_graph_stats_for_query(self, session_id: str, function_name: str) -> dict:
        nodes, edges = self.get_function_graph(session_id, function_name)
        return {
            "query": function_name,
            "nodes": len(nodes),
            "edges": len(edges),
        }

    def reset_session(self, session_id: str) -> None:
        conn = self._connections.pop(session_id, None)
        if conn is not None:
            conn.close()
        db_path = self._session_db_path(session_id)
        if db_path.exists():
            db_path.unlink()
