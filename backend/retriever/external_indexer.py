from collections.abc import Iterable
import csv
from pathlib import Path

import requests

from backend.config.settings import AppConfig


class ExternalKnowledgeIndexer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def fetch_docs(self) -> Iterable[dict]:
        if not self.config.external_knowledge.enabled:
            return []
        chunks = []
        chunks.extend(self._fetch_csv_rows())
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

    def _fetch_csv_rows(self) -> list[dict]:
        csv_path = Path(self.config.external_knowledge.csv_path)
        if not csv_path.exists() or not csv_path.is_file():
            return []

        chunks: list[dict] = []
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                record_id = (row.get("record_id") or "").strip()
                title = (row.get("title") or "").strip()
                content = (row.get("content") or "").strip()
                code_signature = (row.get("code_signature") or "").strip()
                if not record_id or not (title or content):
                    continue

                embedding_text = "\n".join(
                    part
                    for part in [
                        title,
                        content,
                        f"Code signature: {code_signature}" if code_signature else "",
                    ]
                    if part
                )

                chunks.append(
                    {
                        "id": f"kb:{record_id}",
                        "content": embedding_text,
                        "file_path": (row.get("url") or "").strip(),
                        "function_name": code_signature,
                        "type": (row.get("source_type") or "knowledge_base").strip(),
                        "metadata": {
                            "record_id": record_id,
                            "source_type": (row.get("source_type") or "").strip(),
                            "domain": (row.get("domain") or "").strip(),
                            "library": (row.get("library") or "").strip(),
                            "title": title,
                            "content": content,
                            "code_signature": code_signature,
                            "tags": (row.get("tags") or "").strip(),
                            "url": (row.get("url") or "").strip(),
                            "author": (row.get("author") or "").strip(),
                            "date_published": (row.get("date_published") or "").strip(),
                            "votes_or_stars": self._parse_int(row.get("votes_or_stars")),
                            "relevance_label": (row.get("relevance_label") or "").strip().lower(),
                            "difficulty_level": (row.get("difficulty_level") or "").strip().lower(),
                        },
                    }
                )
        return chunks

    @staticmethod
    def _parse_int(value: str | None) -> int:
        if value is None:
            return 0
        try:
            return int(str(value).strip())
        except ValueError:
            return 0
