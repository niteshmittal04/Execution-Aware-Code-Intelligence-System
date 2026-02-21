from pathlib import Path

from backend.config.settings import AppConfig
from backend.embeddings.minilm_embedder import MiniLmEmbedder
from backend.graph.sqlite_graph import SqliteGraphStore
from backend.parser.tree_sitter_parser import TreeSitterCodeParser
from backend.repository.cloner import RepositoryCloner
from backend.retriever.external_indexer import ExternalKnowledgeIndexer
from backend.vector.faiss_store import FaissVectorStore


class IndexingService:
    def __init__(
        self,
        config: AppConfig,
        cloner: RepositoryCloner,
        parser: TreeSitterCodeParser,
        graph_store: SqliteGraphStore,
        embedder: MiniLmEmbedder,
        vector_store: FaissVectorStore,
        external_indexer: ExternalKnowledgeIndexer,
    ) -> None:
        self.config = config
        self.cloner = cloner
        self.parser = parser
        self.graph_store = graph_store
        self.embedder = embedder
        self.vector_store = vector_store
        self.external_indexer = external_indexer

    def index_repository(self, repo_url: str, branch: str | None = None) -> dict:
        repo_path = self.cloner.clone(repo_url, branch)
        return self.index_local_path(repo_path)

    def seed_external_knowledge_if_empty(self) -> dict:
        if not self.config.external_knowledge.enabled:
            return {
                "status": "skipped",
                "reason": "external_knowledge_disabled",
                "vector_count": self.vector_store.total_vectors(),
            }

        if not self.vector_store.is_empty():
            return {
                "status": "skipped",
                "reason": "vector_db_not_empty",
                "vector_count": self.vector_store.total_vectors(),
            }

        external_chunks = list(self.external_indexer.fetch_docs())
        if not external_chunks:
            return {
                "status": "skipped",
                "reason": "no_external_knowledge_rows",
                "vector_count": self.vector_store.total_vectors(),
            }

        try:
            external_embeddings = self.embedder.embed_batch(external_chunks)
            self.vector_store.insert_embeddings(external_embeddings)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "failed",
                "reason": "embedding_error",
                "error": str(exc),
                "vector_count": self.vector_store.total_vectors(),
            }
        return {
            "status": "seeded",
            "seeded_rows": len(external_embeddings),
            "vector_count": self.vector_store.total_vectors(),
        }

    def index_local_path(self, repo_path: Path) -> dict:
        nodes, edges, variables, chunks = self.parser.parse_repository(repo_path)
        self.graph_store.upsert_graph(nodes, edges, variables)

        embedded_chunks: list[dict] = []
        embedding_errors: list[str] = []
        try:
            embedded_chunks = self.embedder.embed_batch(chunks)
            self.vector_store.insert_embeddings(embedded_chunks)
        except Exception as exc:  # noqa: BLE001
            embedding_errors.append(str(exc))

        external_chunks = list(self.external_indexer.fetch_docs())
        external_embeddings_count = 0
        if external_chunks:
            try:
                external_embeddings = self.embedder.embed_batch(external_chunks)
                self.vector_store.insert_embeddings(external_embeddings)
                external_embeddings_count = len(external_embeddings)
            except Exception as exc:  # noqa: BLE001
                embedding_errors.append(str(exc))

        return {
            "repo": str(repo_path),
            "indexed_nodes": len(nodes),
            "indexed_edges": len(edges),
            "indexed_variables": len(variables),
            "indexed_chunks": len(chunks),
            "indexed_chunk_embeddings": len(embedded_chunks),
            "indexed_external_chunks": len(external_chunks),
            "indexed_external_embeddings": external_embeddings_count,
            "partial_indexing": len(embedding_errors) > 0,
            "warnings": embedding_errors,
        }
