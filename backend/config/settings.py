from pathlib import Path

import yaml
from pydantic import BaseModel


class OllamaConfig(BaseModel):
    base_url: str
    llm_model: str
    embedding_model: str
    request_timeout_seconds: int
    max_context_chars: int


class MilvusConfig(BaseModel):
    host: str
    port: int
    collection: str
    search_limit: int
    search_metric: str


class SqliteConfig(BaseModel):
    path: str


class IndexingConfig(BaseModel):
    batch_size: int
    chunk_size: int
    chunk_overlap: int
    max_file_bytes: int
    include_extensions: list[str]
    max_workers: int


class GithubConfig(BaseModel):
    clone_dir: str
    clone_timeout_seconds: int


class GraphConfig(BaseModel):
    traversal_depth: int
    graph_page_size: int


class RuntimeConfig(BaseModel):
    request_timeout_seconds: int
    retry_attempts: int
    retry_backoff_seconds: float
    retry_backoff_multiplier: float


class ExternalKnowledgeConfig(BaseModel):
    enabled: bool
    docs_urls: list[str]
    stackoverflow_tags: list[str]
    github_issue_repos: list[str]


class AppConfig(BaseModel):
    ollama: OllamaConfig
    milvus: MilvusConfig
    sqlite: SqliteConfig
    indexing: IndexingConfig
    github: GithubConfig
    graph: GraphConfig
    runtime: RuntimeConfig
    external_knowledge: ExternalKnowledgeConfig


def _resolve_path(config_path: str | None = None) -> Path:
    if config_path:
        return Path(config_path).resolve()
    return (Path(__file__).resolve().parents[2] / "config.yaml").resolve()


def load_config(config_path: str | None = None) -> AppConfig:
    path = _resolve_path(config_path)
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return AppConfig.model_validate(raw)
