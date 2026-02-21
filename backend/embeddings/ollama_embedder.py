from ollama import Client

from backend.config.settings import AppConfig
from backend.utils.retry import retry_call


class OllamaEmbedder:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = Client(host=self.config.ollama.base_url)

    def embed_text(self, text: str) -> list[float]:
        def _embed() -> list[float]:
            try:
                response = self.client.embed(model=self.config.ollama.embedding_model, input=text)
                return response["embeddings"][0]
            except Exception:  # noqa: BLE001
                response = self.client.embeddings(
                    model=self.config.ollama.embedding_model,
                    prompt=text,
                )
                return response["embedding"]

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
