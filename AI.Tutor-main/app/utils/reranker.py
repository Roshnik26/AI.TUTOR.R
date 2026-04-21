from sentence_transformers import CrossEncoder
from typing import List, Dict
from app.utils.logger import logger

class RerankerService:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Initializing Reranker with model: {model_name}")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[Dict], top_n: int = 5) -> List[Dict]:
        """
        Reranks a list of documents based on their relevance to a query.
        """
        if not documents:
            return []

        logger.info(f"Reranking {len(documents)} documents for query: {query}")

        # Prepare pairs for the Cross-Encoder: (query, document_text)
        pairs = [[query, doc["text"]] for doc in documents]
        
        # Predict relevance scores
        scores = self.model.predict(pairs)

        # Attach scores to documents and sort
        for i, score in enumerate(scores):
            documents[i]["rerank_score"] = float(score)

        # Sort by score in descending order
        reranked_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)

        return reranked_docs[:top_n]
