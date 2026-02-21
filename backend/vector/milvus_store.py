from pymilvus import (  # type: ignore
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from backend.config.settings import AppConfig


class MilvusVectorStore:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.available = False
        try:
            connections.connect(host=self.config.milvus.host, port=str(self.config.milvus.port))
            self.available = True
        except Exception:
            self.available = False
        self.collection_name = self.config.milvus.collection
        self.collection: Collection | None = None

    def _ensure_collection(self, dimension: int) -> None:
        if not self.available:
            return
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=512, is_primary=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="function_name", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        schema = CollectionSchema(fields=fields, description="Execution aware code chunks")
        self.collection = Collection(self.collection_name, schema=schema)
        self.collection.create_index(
            field_name="embedding",
            index_params={
                "metric_type": self.config.milvus.search_metric,
                "index_type": "AUTOINDEX",
                "params": {},
            },
        )
        self.collection.load()

    def insert_embeddings(self, rows: list[dict]) -> None:
        if not rows or not self.available:
            return
        self._ensure_collection(len(rows[0]["embedding"]))
        if self.collection is None:
            return

        batch_size = self.config.indexing.batch_size
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            self.collection.insert(
                [
                    [item["id"] for item in batch],
                    [item["embedding"] for item in batch],
                    [item["content"] for item in batch],
                    [item["file_path"] for item in batch],
                    [item["function_name"] for item in batch],
                    [item["type"] for item in batch],
                    [item["metadata"] for item in batch],
                ]
            )
        self.collection.flush()

    def search(self, embedding: list[float]) -> list[dict]:
        if not self.available:
            return []
        if self.collection is None:
            if not embedding:
                return []
            self._ensure_collection(len(embedding))
        if self.collection is None:
            return []
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding",
            param={"metric_type": self.config.milvus.search_metric, "params": {}},
            limit=self.config.milvus.search_limit,
            output_fields=["content", "file_path", "function_name", "type", "metadata"],
        )
        output: list[dict] = []
        for hit in results[0]:
            output.append(
                {
                    "id": hit.id,
                    "score": hit.score,
                    "content": hit.entity.get("content"),
                    "file_path": hit.entity.get("file_path"),
                    "function_name": hit.entity.get("function_name"),
                    "type": hit.entity.get("type"),
                    "metadata": hit.entity.get("metadata"),
                }
            )
        return output
