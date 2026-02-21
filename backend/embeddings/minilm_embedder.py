from sentence_transformers import SentenceTransformer  # type: ignore

from backend.config.settings import AppConfig
from backend.utils.retry import retry_call


class MiniLmEmbedder:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.model = SentenceTransformer(self.config.embeddings.model_name)

    def embed_text(self, text: str) -> list[float]:
        def _embed() -> list[float]:
            vector = self.model.encode(
                text,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            return vector.tolist()

        return retry_call(
            fn=_embed,
            attempts=self.config.runtime.retry_attempts,
            initial_backoff_seconds=self.config.runtime.retry_backoff_seconds,
            multiplier=self.config.runtime.retry_backoff_multiplier,
        )

    def embed_batch(self, chunks: list[dict]) -> list[dict]:
        out: list[dict] = []
        batch_size = self.config.indexing.batch_size
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            for item in batch:
                embedding = self.embed_text(item["content"])
                out.append({**item, "embedding": embedding})
        return out
