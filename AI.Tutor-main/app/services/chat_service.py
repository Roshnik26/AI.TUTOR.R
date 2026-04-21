from app.llm.mistral_client import MistralService
from app.repository.milvus_repo import MilvusRepository


class ChatService:
    def __init__(self, db):
        self.repo = MilvusRepository(db)
        self.llm = MistralService()

    def chat(self, query: str, query_embedding, top_k: int = 1):
        docs = self.repo.search(query_embedding, top_k)

        if not docs:
            return {"answer": "No relevant information found.", "context": []}

        context = "\n".join([d["text"] for d in docs])
        
        if not docs:
            return {
        "answer": "Not found in the provided documents.",
        "context": [],
        }

        answer = self.llm.generate_response(
            context=context,
            query=query,
        )

        return {
            "answer": answer,
            "context": docs,
        }