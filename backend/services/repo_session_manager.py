import hashlib
import json
import shutil
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.config.settings import AppConfig


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RepoSession:
    session_id: str
    repo_id: str
    repo_path: str
    vector_namespace: str
    graph_namespace: str
    ast_cache_path: str
    created_at: str
    last_accessed: str
    status: str
    indexed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class RepoSessionManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        sqlite_path = Path(self.config.sqlite.path)
        self.session_db_path = sqlite_path.parent / "sessions.db"
        self.session_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.session_db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS repo_sessions (
                session_id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL,
                repo_path TEXT NOT NULL,
                vector_namespace TEXT NOT NULL,
                graph_namespace TEXT NOT NULL,
                ast_cache_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                status TEXT NOT NULL,
                indexed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_repo_structure (
                session_id TEXT PRIMARY KEY,
                structure_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def _repo_id(self, repo_path: Path) -> str:
        normalized = str(repo_path.resolve()).replace("\\", "/").lower()
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
        return f"{repo_path.name}:{digest}"

    def _row_to_session(self, row: sqlite3.Row | None) -> RepoSession | None:
        if row is None:
            return None
        return RepoSession(
            session_id=row["session_id"],
            repo_id=row["repo_id"],
            repo_path=row["repo_path"],
            vector_namespace=row["vector_namespace"],
            graph_namespace=row["graph_namespace"],
            ast_cache_path=row["ast_cache_path"],
            created_at=row["created_at"],
            last_accessed=row["last_accessed"],
            status=row["status"],
            indexed=bool(row["indexed"]),
        )

    def _touch(self, session_id: str) -> None:
        self.conn.execute(
            "UPDATE repo_sessions SET last_accessed = ? WHERE session_id = ?",
            (_utc_now_iso(), session_id),
        )
        self.conn.commit()

    def create_session(self, repo_path: Path) -> RepoSession:
        resolved_repo_path = repo_path.resolve()
        repo_id = self._repo_id(resolved_repo_path)
        now = _utc_now_iso()

        existing = self.conn.execute(
            "SELECT * FROM repo_sessions WHERE repo_id = ? ORDER BY created_at DESC LIMIT 1",
            (repo_id,),
        ).fetchone()

        self.conn.execute("UPDATE repo_sessions SET status = 'closed' WHERE status = 'active'")

        if existing:
            self.conn.execute(
                """
                UPDATE repo_sessions
                SET status = 'active', last_accessed = ?
                WHERE session_id = ?
                """,
                (now, existing["session_id"]),
            )
            self.conn.commit()
            refreshed = self.conn.execute(
                "SELECT * FROM repo_sessions WHERE session_id = ?",
                (existing["session_id"],),
            ).fetchone()
            return self._row_to_session(refreshed)  # type: ignore[return-value]

        session_id = str(uuid.uuid4())
        ast_cache_path = Path("./data/cache") / session_id / "ast"
        ast_cache_path.mkdir(parents=True, exist_ok=True)
        vector_namespace = f"execution_aware_chunks_{session_id}"
        graph_namespace = session_id

        self.conn.execute(
            """
            INSERT INTO repo_sessions (
                session_id, repo_id, repo_path, vector_namespace, graph_namespace,
                ast_cache_path, created_at, last_accessed, status, indexed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', 0)
            """,
            (
                session_id,
                repo_id,
                str(resolved_repo_path),
                vector_namespace,
                graph_namespace,
                str(ast_cache_path.resolve()),
                now,
                now,
            ),
        )
        self.conn.commit()
        created = self.conn.execute(
            "SELECT * FROM repo_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return self._row_to_session(created)  # type: ignore[return-value]

    def get_active_session(self) -> RepoSession | None:
        row = self.conn.execute(
            "SELECT * FROM repo_sessions WHERE status = 'active' ORDER BY last_accessed DESC LIMIT 1"
        ).fetchone()
        session = self._row_to_session(row)
        if session:
            self._touch(session.session_id)
        return session

    def get_session(self, session_id: str) -> RepoSession | None:
        row = self.conn.execute(
            "SELECT * FROM repo_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        session = self._row_to_session(row)
        if session and session.status == "active":
            self._touch(session.session_id)
        return session

    def switch_session(self, repo_path: Path) -> RepoSession:
        return self.create_session(repo_path)

    def close_session(self, session_id: str) -> None:
        self.conn.execute(
            "UPDATE repo_sessions SET status = 'closed', last_accessed = ? WHERE session_id = ?",
            (_utc_now_iso(), session_id),
        )
        self.conn.commit()

    def reset_session(self, session_id: str) -> RepoSession | None:
        session = self.get_session(session_id)
        if not session:
            return None

        cache_root = Path("./data/cache") / session_id
        if cache_root.exists():
            shutil.rmtree(cache_root, ignore_errors=True)

        graph_root = Path("./data/graph_storage") / session_id
        if graph_root.exists():
            shutil.rmtree(graph_root, ignore_errors=True)

        faiss_root = Path(self.config.faiss.index_path).parent / "sessions" / session_id
        if faiss_root.exists():
            shutil.rmtree(faiss_root, ignore_errors=True)

        ast_cache_path = Path("./data/cache") / session_id / "ast"
        ast_cache_path.mkdir(parents=True, exist_ok=True)

        self.conn.execute(
            """
            UPDATE repo_sessions
            SET indexed = 0,
                ast_cache_path = ?,
                last_accessed = ?,
                status = 'active'
            WHERE session_id = ?
            """,
            (str(ast_cache_path.resolve()), _utc_now_iso(), session_id),
        )
        self.conn.execute(
            "DELETE FROM session_repo_structure WHERE session_id = ?",
            (session_id,),
        )
        self.conn.commit()
        return self.get_session(session_id)

    def mark_indexed(self, session_id: str, indexed: bool = True) -> None:
        self.conn.execute(
            "UPDATE repo_sessions SET indexed = ?, last_accessed = ? WHERE session_id = ?",
            (1 if indexed else 0, _utc_now_iso(), session_id),
        )
        self.conn.commit()

    def get_cached_structure(self, session_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT structure_json FROM session_repo_structure WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row["structure_json"])
        except Exception:
            return None

    def store_structure(self, session_id: str, structure: dict) -> None:
        serialized = json.dumps(structure, ensure_ascii=False)
        self.conn.execute(
            """
            INSERT INTO session_repo_structure (session_id, structure_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                structure_json = excluded.structure_json,
                updated_at = excluded.updated_at
            """,
            (session_id, serialized, _utc_now_iso()),
        )
        self.conn.commit()
