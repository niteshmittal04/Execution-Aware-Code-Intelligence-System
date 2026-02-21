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
        self.index_path = Path(self.config.faiss.index_path)
        self.metadata_path = Path(self.config.faiss.metadata_path)
        self.index: faiss.IndexFlatIP | None = None
        self.dimension: int | None = None
        self.ids: list[str] = []
        self.rows_by_id: dict[str, dict] = {}
        self._load_existing_index()

    def total_vectors(self) -> int:
        if self.index is None:
            return 0
        return int(self.index.ntotal)

    def is_empty(self) -> bool:
        return self.total_vectors() == 0

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        normalized = vectors.copy()
        faiss.normalize_L2(normalized)
        return normalized

    def _load_existing_index(self) -> None:
        if not self.index_path.exists() or not self.metadata_path.exists():
            return
        try:
            self.index = faiss.read_index(str(self.index_path))
            raw_metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            self.dimension = int(raw_metadata.get("dimension") or 0) or None
            self.ids = [str(item) for item in raw_metadata.get("ids", [])]
            rows = raw_metadata.get("rows_by_id", {})
            if isinstance(rows, dict):
                self.rows_by_id = {str(key): value for key, value in rows.items()}
            if self.index is not None and len(self.ids) != self.index.ntotal:
                self.index = None
                self.dimension = None
                self.ids = []
                self.rows_by_id = {}
        except Exception:
            self.index = None
            self.dimension = None
            self.ids = []
            self.rows_by_id = {}

    def _persist(self) -> None:
        if self.index is None or self.dimension is None:
            return
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        payload = {
            "dimension": self.dimension,
            "ids": self.ids,
            "rows_by_id": self.rows_by_id,
        }
        self.metadata_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def insert_embeddings(self, rows: list[dict]) -> None:
        if not rows or not self.available:
            return

        filtered_rows = [row for row in rows if row.get("id") and row["id"] not in self.rows_by_id]
        if not filtered_rows:
            return

        vectors = np.array([row["embedding"] for row in filtered_rows], dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] == 0:
            return

        current_dimension = int(vectors.shape[1])
        if self.index is None:
            self.index = faiss.IndexFlatIP(current_dimension)
            self.dimension = current_dimension

        if self.dimension != current_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {current_dimension}"
            )

        normalized_vectors = self._normalize(vectors)
        self.index.add(normalized_vectors)

        for row in filtered_rows:
            row_id = row["id"]
            self.ids.append(row_id)
            self.rows_by_id[row_id] = {
                "content": row.get("content"),
                "file_path": row.get("file_path"),
                "function_name": row.get("function_name"),
                "type": row.get("type"),
                "metadata": row.get("metadata"),
            }

        self._persist()

    def search(self, embedding: list[float], filters: dict | None = None) -> list[dict]:
        if not self.available or not embedding or self.index is None:
            return []

        query = np.array([embedding], dtype=np.float32)
        if query.ndim != 2 or query.shape[1] == 0:
            return []

        if self.dimension is not None and query.shape[1] != self.dimension:
            return []

        normalized_query = self._normalize(query)
        limit = min(self.search_limit, self.index.ntotal)
        if limit <= 0:
            return []

        scores, indices = self.index.search(normalized_query, limit)
        output: list[dict] = []
        for score, vector_index in zip(scores[0], indices[0], strict=False):
            if vector_index < 0 or vector_index >= len(self.ids):
                continue
            row_id = self.ids[vector_index]
            row = self.rows_by_id.get(row_id, {})
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
