import json
import sqlite3
from pathlib import Path

from backend.config.settings import AppConfig
from backend.parser.tree_sitter_parser import ParsedEdge, ParsedSymbol, ParsedVariable


class SqliteGraphStore:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        db_path = Path(self.config.sqlite.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
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
        self.conn.execute(
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
        self.conn.execute(
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
        self.conn.commit()

    def upsert_graph(
        self,
        nodes: list[ParsedSymbol],
        edges: list[ParsedEdge],
        variables: list[ParsedVariable],
    ) -> None:
        batch_size = self.config.indexing.batch_size
        for start in range(0, len(nodes), batch_size):
            batch = nodes[start : start + batch_size]
            self.conn.executemany(
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
            self.conn.commit()

        for start in range(0, len(edges), batch_size):
            batch = edges[start : start + batch_size]
            self.conn.executemany(
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
            self.conn.commit()

        for start in range(0, len(variables), batch_size):
            batch = variables[start : start + batch_size]
            self.conn.executemany(
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
            self.conn.commit()

    def get_function_graph(self, function_name: str) -> tuple[list[dict], list[dict]]:
        depth = self.config.graph.traversal_depth
        page_size = self.config.graph.graph_page_size

        seed_rows = self.conn.execute(
            "SELECT * FROM nodes WHERE name = ? LIMIT ?", (function_name, page_size)
        ).fetchall()
        seen_nodes = {row["id"]: dict(row) for row in seed_rows}
        frontier = [row["id"] for row in seed_rows]
        all_edges: dict[str, dict] = {}

        for _ in range(depth):
            if not frontier:
                break
            placeholders = ",".join(["?"] * len(frontier))
            edge_rows = self.conn.execute(
                f"""
                SELECT * FROM edges
                WHERE source IN ({placeholders}) OR target IN ({placeholders})
                LIMIT ?
                """,
                (*frontier, *frontier, page_size),
            ).fetchall()
            all_edges.update({row["id"]: dict(row) for row in edge_rows})

            next_frontier = set()
            for edge in edge_rows:
                next_frontier.add(edge["source"])
                next_frontier.add(edge["target"])

            if next_frontier:
                placeholders = ",".join(["?"] * len(next_frontier))
                node_rows = self.conn.execute(
                    f"SELECT * FROM nodes WHERE id IN ({placeholders}) LIMIT ?",
                    (*next_frontier, page_size),
                ).fetchall()
                for row in node_rows:
                    seen_nodes[row["id"]] = dict(row)

            frontier = [node for node in next_frontier if node not in seen_nodes]

        return list(seen_nodes.values()), list(all_edges.values())

    def get_variables_for_scope(self, function_name: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM variables WHERE scope LIKE ? LIMIT ?",
            (f"%{function_name}%", self.config.graph.graph_page_size),
        ).fetchall()
        return [dict(row) for row in rows]
