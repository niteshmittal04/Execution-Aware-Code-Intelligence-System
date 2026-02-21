import os

from pydantic import BaseModel
from dotenv import load_dotenv


class OllamaConfig(BaseModel):
    base_url: str
    llm_model: str
    embedding_model: str
    request_timeout_seconds: int
    max_context_chars: int


class LlmConfig(BaseModel):
    base_url: str
    model: str
    api_key_env_var: str
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
    llm: LlmConfig
    milvus: MilvusConfig
    sqlite: SqliteConfig
    indexing: IndexingConfig
    github: GithubConfig
    graph: GraphConfig
    runtime: RuntimeConfig
    external_knowledge: ExternalKnowledgeConfig


def _getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _getenv_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _getenv_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _getenv_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config(config_path: str | None = None) -> AppConfig:
    load_dotenv()

    return AppConfig(
        ollama=OllamaConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            llm_model=os.getenv("OLLAMA_LLM_MODEL", "ministral-3:3b"),
            embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "dengcao/Qwen3-Embedding-8B:Q8_0"),
            request_timeout_seconds=_getenv_int("OLLAMA_REQUEST_TIMEOUT_SECONDS", 90),
            max_context_chars=_getenv_int("OLLAMA_MAX_CONTEXT_CHARS", 32000),
        ),
        llm=LlmConfig(
            base_url=os.getenv("LLM_BASE_URL", "https://ai.megallm.io/v1"),
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929|"),
            api_key_env_var=os.getenv("LLM_API_KEY_ENV_VAR", "MEGALLM_API_KEY"),
            max_context_chars=_getenv_int("LLM_MAX_CONTEXT_CHARS", 32000),
        ),
        milvus=MilvusConfig(
            host=os.getenv("MILVUS_HOST", "localhost"),
            port=_getenv_int("MILVUS_PORT", 19530),
            collection=os.getenv("MILVUS_COLLECTION", "execution_aware_chunks"),
            search_limit=_getenv_int("MILVUS_SEARCH_LIMIT", 8),
            search_metric=os.getenv("MILVUS_SEARCH_METRIC", "COSINE"),
        ),
        sqlite=SqliteConfig(
            path=os.getenv("SQLITE_PATH", "./data/sqlite/graph.db"),
        ),
        indexing=IndexingConfig(
            batch_size=_getenv_int("INDEXING_BATCH_SIZE", 24),
            chunk_size=_getenv_int("INDEXING_CHUNK_SIZE", 1200),
            chunk_overlap=_getenv_int("INDEXING_CHUNK_OVERLAP", 120),
            max_file_bytes=_getenv_int("INDEXING_MAX_FILE_BYTES", 1048576),
            include_extensions=_getenv_list("INDEXING_INCLUDE_EXTENSIONS", [".py"]),
            max_workers=_getenv_int("INDEXING_MAX_WORKERS", 4),
        ),
        github=GithubConfig(
            clone_dir=os.getenv("GITHUB_CLONE_DIR", "./data/repos"),
            clone_timeout_seconds=_getenv_int("GITHUB_CLONE_TIMEOUT_SECONDS", 240),
        ),
        graph=GraphConfig(
            traversal_depth=_getenv_int("GRAPH_TRAVERSAL_DEPTH", 3),
            graph_page_size=_getenv_int("GRAPH_PAGE_SIZE", 100),
        ),
        runtime=RuntimeConfig(
            request_timeout_seconds=_getenv_int("RUNTIME_REQUEST_TIMEOUT_SECONDS", 90),
            retry_attempts=_getenv_int("RUNTIME_RETRY_ATTEMPTS", 3),
            retry_backoff_seconds=_getenv_float("RUNTIME_RETRY_BACKOFF_SECONDS", 1.0),
            retry_backoff_multiplier=_getenv_float("RUNTIME_RETRY_BACKOFF_MULTIPLIER", 2.0),
        ),
        external_knowledge=ExternalKnowledgeConfig(
            enabled=_getenv_bool("EXTERNAL_KNOWLEDGE_ENABLED", False),
            docs_urls=_getenv_list("EXTERNAL_KNOWLEDGE_DOCS_URLS", []),
            stackoverflow_tags=_getenv_list("EXTERNAL_KNOWLEDGE_STACKOVERFLOW_TAGS", ["python"]),
            github_issue_repos=_getenv_list("EXTERNAL_KNOWLEDGE_GITHUB_ISSUE_REPOS", []),
        ),
    )
