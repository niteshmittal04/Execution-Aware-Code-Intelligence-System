from pathlib import Path

from backend.config.settings import AppConfig
from backend.embeddings.minilm_embedder import MiniLmEmbedder
from backend.graph.sqlite_graph import SqliteGraphStore
from backend.parser.tree_sitter_parser import TreeSitterCodeParser
from backend.repository.cloner import RepositoryCloner
from backend.retriever.external_indexer import ExternalKnowledgeIndexer
from backend.services.repo_session_manager import RepoSessionManager
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
        session_manager: RepoSessionManager,
    ) -> None:
        self.config = config
        self.cloner = cloner
        self.parser = parser
        self.graph_store = graph_store
        self.embedder = embedder
        self.vector_store = vector_store
        self.external_indexer = external_indexer
        self.session_manager = session_manager

    def index_repository(
        self,
        session_id: str,
        repo_url: str | None = None,
        branch: str | None = None,
        reindex: bool = False,
    ) -> dict:
        session = self.session_manager.get_session(session_id)
        if session is None:
            raise ValueError("Invalid session_id.")

        if repo_url:
            repo_path = self.cloner.clone(repo_url, branch)
            if Path(session.repo_path).resolve() != repo_path.resolve():
                raise ValueError("Session repository does not match the provided repo_url.")
        else:
            repo_path = Path(session.repo_path)

        return self.index_local_path(session_id=session_id, repo_path=repo_path, reindex=reindex)

    def seed_external_knowledge_if_empty(self, session_id: str) -> dict:
        if not self.config.external_knowledge.enabled:
            return {
                "status": "skipped",
                "reason": "external_knowledge_disabled",
                "vector_count": self.vector_store.total_vectors(session_id),
            }

        if not self.vector_store.is_empty(session_id):
            return {
                "status": "skipped",
                "reason": "vector_db_not_empty",
                "vector_count": self.vector_store.total_vectors(session_id),
            }

        external_chunks = list(self.external_indexer.fetch_docs())
        if not external_chunks:
            return {
                "status": "skipped",
                "reason": "no_external_knowledge_rows",
                "vector_count": self.vector_store.total_vectors(session_id),
            }

        try:
            external_embeddings = self.embedder.embed_batch(external_chunks)
            self.vector_store.insert_embeddings(session_id, external_embeddings)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "failed",
                "reason": "embedding_error",
                "error": str(exc),
                "vector_count": self.vector_store.total_vectors(session_id),
            }
        return {
            "status": "seeded",
            "seeded_rows": len(external_embeddings),
            "vector_count": self.vector_store.total_vectors(session_id),
        }

    def index_local_path(self, session_id: str, repo_path: Path, reindex: bool = False) -> dict:
        session = self.session_manager.get_session(session_id)
        if session is None:
            raise ValueError("Invalid session_id.")

        if session.indexed and not reindex:
            return {
                "repo": str(repo_path),
                "session_id": session_id,
                "status": "reused",
                "indexed_nodes": 0,
                "indexed_edges": 0,
                "indexed_variables": 0,
                "indexed_chunks": 0,
                "indexed_chunk_embeddings": 0,
                "indexed_external_chunks": 0,
                "indexed_external_embeddings": 0,
                "partial_indexing": False,
                "warnings": [],
            }

        nodes, edges, variables, chunks = self.parser.parse_repository(repo_path)
        self.graph_store.upsert_graph(session_id, nodes, edges, variables)

        embedded_chunks: list[dict] = []
        embedding_errors: list[str] = []
        try:
            embedded_chunks = self.embedder.embed_batch(chunks)
            self.vector_store.insert_embeddings(session_id, embedded_chunks)
        except Exception as exc:  # noqa: BLE001
            embedding_errors.append(str(exc))

        external_chunks = list(self.external_indexer.fetch_docs())
        external_embeddings_count = 0
        if external_chunks:
            try:
                external_embeddings = self.embedder.embed_batch(external_chunks)
                self.vector_store.insert_embeddings(session_id, external_embeddings)
                external_embeddings_count = len(external_embeddings)
            except Exception as exc:  # noqa: BLE001
                embedding_errors.append(str(exc))

        self.session_manager.mark_indexed(session_id, indexed=True)

        return {
            "repo": str(repo_path),
            "session_id": session_id,
            "status": "indexed",
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
