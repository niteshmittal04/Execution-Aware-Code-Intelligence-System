from collections.abc import Iterable

import requests

from backend.config.settings import AppConfig


class ExternalKnowledgeIndexer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def fetch_docs(self) -> Iterable[dict]:
        if not self.config.external_knowledge.enabled:
            return []
        chunks = []
        timeout = self.config.runtime.request_timeout_seconds
        for url in self.config.external_knowledge.docs_urls:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            chunks.append(
                {
                    "id": f"docs:{url}",
                    "content": response.text,
                    "file_path": url,
                    "function_name": "",
                    "type": "documentation",
                    "metadata": {"source": "docs"},
                }
            )
        return chunks
