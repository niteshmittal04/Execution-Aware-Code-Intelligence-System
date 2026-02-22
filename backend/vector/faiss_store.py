import json
from pathlib import Path

import faiss  # type: ignore
import numpy as np

from backend.config.settings import AppConfig


class FaissVectorStore:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.available = True
        self.search_limit = self.config.faiss.search_limit
        self.base_index_path = Path(self.config.faiss.index_path)
        self.base_metadata_path = Path(self.config.faiss.metadata_path)
        self._session_data: dict[str, dict] = {}

    def _session_paths(self, session_id: str) -> tuple[Path, Path]:
        session_root = self.base_index_path.parent / "sessions" / session_id
        session_root.mkdir(parents=True, exist_ok=True)
        collection_name = f"{self.base_index_path.stem}_{session_id}"
        metadata_name = f"{self.base_metadata_path.stem}_{session_id}"
        return (
            session_root / f"{collection_name}{self.base_index_path.suffix}",
            session_root / f"{metadata_name}{self.base_metadata_path.suffix}",
        )

    def _get_session_data(self, session_id: str) -> dict:
        existing = self._session_data.get(session_id)
        if existing is not None:
            return existing

        index_path, metadata_path = self._session_paths(session_id)
        payload = {
            "index_path": index_path,
            "metadata_path": metadata_path,
            "index": None,
            "dimension": None,
            "ids": [],
            "rows_by_id": {},
        }
        self._load_existing_index(payload)
        self._session_data[session_id] = payload
        return payload

    def total_vectors(self, session_id: str) -> int:
        data = self._get_session_data(session_id)
        if data["index"] is None:
            return 0
        return int(data["index"].ntotal)

    def is_empty(self, session_id: str) -> bool:
        return self.total_vectors(session_id) == 0

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        normalized = vectors.copy()
        faiss.normalize_L2(normalized)
        return normalized

    def _load_existing_index(self, data: dict) -> None:
        index_path: Path = data["index_path"]
        metadata_path: Path = data["metadata_path"]
        if not index_path.exists() or not metadata_path.exists():
            return
        try:
            data["index"] = faiss.read_index(str(index_path))
            raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            data["dimension"] = int(raw_metadata.get("dimension") or 0) or None
            data["ids"] = [str(item) for item in raw_metadata.get("ids", [])]
            rows = raw_metadata.get("rows_by_id", {})
            if isinstance(rows, dict):
                data["rows_by_id"] = {str(key): value for key, value in rows.items()}
            if data["index"] is not None and len(data["ids"]) != data["index"].ntotal:
                data["index"] = None
                data["dimension"] = None
                data["ids"] = []
                data["rows_by_id"] = {}
        except Exception:
            data["index"] = None
            data["dimension"] = None
            data["ids"] = []
            data["rows_by_id"] = {}

    def _persist(self, data: dict) -> None:
        if data["index"] is None or data["dimension"] is None:
            return
        index_path: Path = data["index_path"]
        metadata_path: Path = data["metadata_path"]
        index_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(data["index"], str(index_path))
        payload = {
            "dimension": data["dimension"],
            "ids": data["ids"],
            "rows_by_id": data["rows_by_id"],
        }
        metadata_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def insert_embeddings(self, session_id: str, rows: list[dict]) -> None:
        if not rows or not self.available:
            return
        data = self._get_session_data(session_id)

        filtered_rows = [
            row for row in rows if row.get("id") and row["id"] not in data["rows_by_id"]
        ]
        if not filtered_rows:
            return

        vectors = np.array([row["embedding"] for row in filtered_rows], dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] == 0:
            return

        current_dimension = int(vectors.shape[1])
        if data["index"] is None:
            data["index"] = faiss.IndexFlatIP(current_dimension)
            data["dimension"] = current_dimension

        if data["dimension"] != current_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {data['dimension']}, got {current_dimension}"
            )

        normalized_vectors = self._normalize(vectors)
        data["index"].add(normalized_vectors)

        for row in filtered_rows:
            row_id = row["id"]
            data["ids"].append(row_id)
            data["rows_by_id"][row_id] = {
                "content": row.get("content"),
                "file_path": row.get("file_path"),
                "function_name": row.get("function_name"),
                "type": row.get("type"),
                "metadata": row.get("metadata"),
            }

        self._persist(data)

    def search(self, session_id: str, embedding: list[float], filters: dict | None = None) -> list[dict]:
        data = self._get_session_data(session_id)
        if not self.available or not embedding or data["index"] is None:
            return []

        query = np.array([embedding], dtype=np.float32)
        if query.ndim != 2 or query.shape[1] == 0:
            return []

        if data["dimension"] is not None and query.shape[1] != data["dimension"]:
            return []

        normalized_query = self._normalize(query)
        limit = min(self.search_limit, data["index"].ntotal)
        if limit <= 0:
            return []

        scores, indices = data["index"].search(normalized_query, limit)
        output: list[dict] = []
        for score, vector_index in zip(scores[0], indices[0], strict=False):
            if vector_index < 0 or vector_index >= len(data["ids"]):
                continue
            row_id = data["ids"][vector_index]
            row = data["rows_by_id"].get(row_id, {})
            metadata = row.get("metadata") or {}
            if filters and not self._matches_filters(metadata, filters):
                continue
            output.append(
                {
                    "id": row_id,
                    "score": float(score),
                    "content": row.get("content"),
                    "file_path": row.get("file_path"),
                    "function_name": row.get("function_name"),
                    "type": row.get("type"),
                    "metadata": metadata,
                }
            )
        return self._rerank_hits(output)

    def reset_session(self, session_id: str) -> None:
        data = self._session_data.pop(session_id, None)
        if not data:
            index_path, metadata_path = self._session_paths(session_id)
            data = {"index_path": index_path, "metadata_path": metadata_path}

        index_path = data.get("index_path")
        metadata_path = data.get("metadata_path")
        if isinstance(index_path, Path) and index_path.exists():
            index_path.unlink()
        if isinstance(metadata_path, Path) and metadata_path.exists():
            metadata_path.unlink()

    def _matches_filters(self, metadata: dict, filters: dict) -> bool:
        for key, expected in filters.items():
            if expected is None:
                continue
            actual = metadata.get(key)
            if actual is None:
                return False
            if str(actual).strip().lower() != str(expected).strip().lower():
                return False
        return True

    def _rerank_hits(self, hits: list[dict]) -> list[dict]:
        if not hits:
            return hits
        relevance_boost = {
            "high": 0.08,
            "medium": 0.03,
            "low": 0.0,
        }
        for hit in hits:
            metadata = hit.get("metadata") or {}
            votes = metadata.get("votes_or_stars", 0)
            try:
                votes_value = max(float(votes), 0.0)
            except (TypeError, ValueError):
                votes_value = 0.0
            vote_boost = min(votes_value / 10000.0, 0.12)
            relevance_label = str(metadata.get("relevance_label", "")).strip().lower()
            hit["score"] = float(hit.get("score", 0.0)) + vote_boost + relevance_boost.get(
                relevance_label,
                0.0,
            )
        hits.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        return hits[: self.search_limit]
