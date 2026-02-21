from backend.embeddings.ollama_embedder import OllamaEmbedder
from backend.graph.sqlite_graph import SqliteGraphStore
from backend.vector.milvus_store import MilvusVectorStore


class HybridRetriever:
    def __init__(
        self,
        graph_store: SqliteGraphStore,
        vector_store: MilvusVectorStore,
        embedder: OllamaEmbedder,
    ) -> None:
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(self, function_name: str) -> dict:
        graph_nodes, graph_edges = self.graph_store.get_function_graph(function_name)
        semantic_hits: list[dict] = []
        try:
            vector_query = self.embedder.embed_text(function_name)
            semantic_hits = self.vector_store.search(vector_query)
        except Exception:
            semantic_hits = []
        variable_rows = self.graph_store.get_variables_for_scope(function_name)
        return {
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            "semantic_hits": semantic_hits,
            "variables": variable_rows,
        }
