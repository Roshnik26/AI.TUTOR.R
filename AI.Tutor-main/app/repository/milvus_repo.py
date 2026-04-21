from typing import List,Dict
from app.database.milvus_db import MilvusDB

class MilvusRepository:
    def __init__(self, db):
        self.db = db
        
    def add_documents(
        self,
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict],
    ) -> None:
        self.db.collection.flush()
        self.db.insert(embeddings, texts, metadatas)
        
    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
    ):
        return self.db.search(embedding, top_k)
    
    def insert(
        self,
        embeddings: list[float],
        texts: list,
        metadatas: list,    
    ): 
        self.collection.insert(
            embeddings,
            texts,
            metadatas
        )
        self.collection.flush()
        
    def delete_by_filename(self, filename:str) -> int:
        return self.db.delete_by_filename(filename)
        