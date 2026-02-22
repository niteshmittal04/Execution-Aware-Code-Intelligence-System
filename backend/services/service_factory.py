from functools import lru_cache

from backend.config.settings import load_config
from backend.embeddings.minilm_embedder import MiniLmEmbedder
from backend.graph.sqlite_graph import SqliteGraphStore
from backend.llm.explanation_engine import ExplanationEngine
from backend.parser.tree_sitter_parser import TreeSitterCodeParser
from backend.repository.cloner import RepositoryCloner
from backend.retriever.external_indexer import ExternalKnowledgeIndexer
from backend.retriever.hybrid_retriever import HybridRetriever
from backend.services.indexing_service import IndexingService
from backend.services.repo_session_manager import RepoSessionManager
from backend.services.repo_structure_service import RepoStructureService
from backend.vector.faiss_store import FaissVectorStore


@lru_cache(maxsize=1)
def get_services() -> dict:
    config = load_config()
    cloner = RepositoryCloner(config)
    parser = TreeSitterCodeParser(config)
    graph_store = SqliteGraphStore(config)
    embedder = MiniLmEmbedder(config)
    vector_store = FaissVectorStore(config)
    external_indexer = ExternalKnowledgeIndexer(config)
    session_manager = RepoSessionManager(config)
    structure_service = RepoStructureService(parser, session_manager)
    retriever = HybridRetriever(graph_store, vector_store, embedder)
    llm_engine = ExplanationEngine(config)
    indexing_service = IndexingService(
        config,
        cloner,
        parser,
        graph_store,
        embedder,
        vector_store,
        external_indexer,
        session_manager,
    )
    return {
        "config": config,
        "indexing_service": indexing_service,
        "retriever": retriever,
        "llm_engine": llm_engine,
        "graph_store": graph_store,
        "vector_store": vector_store,
        "session_manager": session_manager,
        "structure_service": structure_service,
    }
