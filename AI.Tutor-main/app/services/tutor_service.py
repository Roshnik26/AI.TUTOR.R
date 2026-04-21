from app.utils.logger import logger
from typing import Dict, List
import json
from app.repository.milvus_repo import MilvusRepository
from app.llm.mistral_client import MistralService
from app.utils.reranker import RerankerService

class TutorService:
    def __init__(self, db):
        self.repo = MilvusRepository(db)
        self.llm = MistralService()
        self.reranker = RerankerService()
        logger.info("TutorService initialized")

    def _get_context(self, query: str, query_embedding, top_k: int = 5) -> str:
        candidate_count = max(top_k * 3, 15) 
        initial_docs = self.repo.search(query_embedding, top_k=candidate_count)

        if not initial_docs:
            return ""

        docs = self.reranker.rerank(query, initial_docs, top_n=top_k)
        
        context_blocks = []
        for doc in docs:
            context_blocks.append(f"{doc['text']}")
        return "\n\n".join(context_blocks)

    def generate_quiz(self, topic: str, query_embedding, top_k: int = 5) -> Dict:
        logger.info(f"Generating quiz for topic: {topic}")
        context = self._get_context(topic, query_embedding, top_k)
        
        if not context:
            return {"status": "failed", "message": "No context found to generate quiz."}
        
        try:
            quiz_str = self.llm.generate_quiz(context=context, num_questions=3)
            # Find JSON block if there's markdown formatting
            if "```json" in quiz_str:
                quiz_str = quiz_str.split("```json")[1].split("```")[0].strip()
            elif "```" in quiz_str:
                quiz_str = quiz_str.split("```")[1].strip()

            quiz_json = json.loads(quiz_str)
            return {"status": "success", "quiz": quiz_json}
        except Exception as e:
            logger.error(f"Failed to generate quiz: {e}")
            return {"status": "failed", "message": "Failed to parse quiz from LLM."}

    def chat_tutor(self, query: str, query_embedding, top_k: int = 5) -> Dict:
        logger.info(f"Tutor chat query received: {query}")
        
        context = self._get_context(query, query_embedding, top_k)
        if not context:
            context = "No relevant documents found. Please answer based on general knowledge but stay encouraging."
            
        answer = self.llm.tutor_response(
            context=context,
            query=query,
        )
        
        return {
            "answer": answer
        }
