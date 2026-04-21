from app.config.settings import settings
from typing import List
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)

from app.config.settings import settings


class MilvusDB:
    def __init__(self):
        self.alias = "default"
        self.collection_name = settings.MILVUS_COLLECTION_NAME

        self._connect()
        self.collection = self._get_or_create_collection()

    def _connect(self):
        try:
            # Use local SQLite-based Milvus Lite so it can deploy on Render for free without Docker
            connections.connect(
                alias=self.alias,
                uri="./milvus_demo.db"
            )
        except Exception as e:
            print(f"Failed to connect to Milvus Lite: {e}")

    def _get_or_create_collection(self) -> Collection:
        if utility.has_collection(self.collection_name):
            collection = Collection(self.collection_name)
            collection.load()
            return collection

        id_field = FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True,
        )

        embedding_field = FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=settings.VECTOR_DIMENSION,
        )

        text_field = FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=65535,
        )

        meta_field = FieldSchema(
            name="metadata",
            dtype=DataType.JSON,
        )

        schema = CollectionSchema(
            fields=[id_field, embedding_field, text_field, meta_field],
            description="Vector search collection",
        )

        collection = Collection(
            name=self.collection_name,
            schema=schema,
        )

        self._create_index(collection)
        collection.load()
        return collection

    def _create_index(self, collection: Collection):
        index_params = {
            "index_type": settings.INDEX_TYPE,
            "metric_type": settings.METRIC_TYPE,
            "params": {"nlist": settings.NLIST},
        }

        collection.create_index(
            field_name="embedding",
            index_params=index_params,
        )

    def insert(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: List[dict],
    ):
        data = [
            embeddings,
            texts,
            metadatas,
        ]

        self.collection.insert(data)
        self.collection.flush()

    def search(self, query_embedding, top_k: int = 1):
        search_params = {"metric_type": settings.METRIC_TYPE}

        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "metadata"],
    )

        formatted_results = []

        for hit in results[0]:
            formatted_results.append({
            "text": hit.entity.get("text"),
            "metadata": hit.entity.get("metadata"),
        })

        return formatted_results
    
    def delete_by_filename(self, filename:str) ->int:
        expr = f'metadata["filename"] == "{filename}"'
        
        result = self.collection.delete(expr=expr)
        self.collection.flush()
        
        return result.delete_count

