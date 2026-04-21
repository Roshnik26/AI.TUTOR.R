from app.utils.logger import logger
from typing import Dict, List
from app.repository.milvus_repo import MilvusRepository
from app.llm.mistral_client import MistralService
from app.utils.embeddings import embed_texts
from app.utils.reranker import RerankerService

class FileUploadService:
    def __init__(self, db):
        self.repo = MilvusRepository(db)
        self.llm = MistralService()
        self.reranker = RerankerService()
        logger.info("FileUploadService initialized with Unstructured and Reranker integration")   
        
    def upload_file_from_elements(
        self,
        filename: str,
        elements: List,
        base_metadata: Dict,
    ) -> Dict:
        """
        Processes elements (chunks) from Unstructured, embeds them, 
        and stores them in Milvus with rich metadata.
        """
        logger.info(f"Processing and indexing elements for file: {filename}")
        
        # Extract text and enriched metadata from each Unstructured element
        chunks_text = [str(el) for el in elements]
        enriched_metadatas = []
        
        for el in elements:
            # Capturing specific Unstructured metadata (page, element type, etc.)
            el_metadata = el.metadata.to_dict() if hasattr(el, 'metadata') else {}
            item_metadata = {
                **base_metadata,
                "filename": filename,
                "element_type": el.__class__.__name__,
                "page_number": el_metadata.get("page_number"),
                "category": getattr(el, 'category', 'NarrativeText')
            }
            enriched_metadatas.append(item_metadata)

        if not chunks_text:
            logger.warning("No text extracted from elements")
            return {
                "status": "failed",
                "reason": "no text extracted",
            }
            
        # Batch Embeddings (Efficient for 1000+ files)
        embeddings = embed_texts(chunks_text)
            
        # Bulk Insert into Milvus
        self.repo.add_documents(
            embeddings=embeddings,
            texts=chunks_text,
            metadatas=enriched_metadatas
        )
        
        logger.info(f"File indexed successfully: {filename}, elements={len(elements)}")
        
        return {
            "status": "success",
            "filename": filename,
            "elements_processed": len(elements),
        }

    def search(self, query_embedding, top_k: int = 1) -> List[Dict]:
        logger.info(f"Searching vectors (top_k={top_k})")
        return self.repo.search(query_embedding, top_k)

    def search_reranked(self, query: str, query_embedding, top_k: int = 5) -> List[Dict]:
        """
        High-accuracy search that uses Milvus for retrieval and a Cross-Encoder for ranking.
        """
        logger.info(f"High-accuracy search for: {query}")
        
        # 1. Fetch more candidates (e.g. 20) to find the best top_k
        initial_docs = self.search(query_embedding, top_k=max(top_k * 4, 20))
        
        if not initial_docs:
            return []

        # 2. Rerank them
        return self.reranker.rerank(query, initial_docs, top_n=top_k)

    def chat(self, query: str, query_embedding, top_k: int = 5) -> Dict:
        logger.info(f"Chat query received: {query}")
        
        # 1. RETRIEVE: Fetch a larger candidate set for re-ranking (e.g., top 15)
        candidate_count = max(top_k * 3, 15) 
        initial_docs = self.search(query_embedding, top_k=candidate_count)

        if not initial_docs:
            logger.warning("No relevant documents found in initial search")
            return {
                "answer": "No relevant information found.",
                "context": [],
            }

        # 2. RE-RANK: Use the Cross-Encoder to find the absolute best top_k
        docs = self.reranker.rerank(query, initial_docs, top_n=top_k)

        # 3. GENERATE: Format context and send to LLM
        context_blocks = []
        for doc in docs:
            meta = doc.get("metadata", {})
            source = meta.get("filename", "Unknown File")
            page = meta.get("page_number", "Unknown Page")
            score = round(doc.get("rerank_score", 0), 4)
            context_blocks.append(f"--- SOURCE: {source} (Page {page}) [Rel: {score}] ---\n{doc['text']}")
        
        context = "\n\n".join(context_blocks)

        answer = self.llm.generate_response(
            context=context,
            query=query,
        )
        
        logger.info("Chat response generated successfully with re-ranking")

        return {
            "answer": answer,
            "context": docs,
        }
        
    def delete_file(self, filename:str) -> int:
        logger.info(f"Deleting file vectors for filename = {filename}")
        deleted_count = self.repo.delete_by_filename(filename)
        logger.info(f"Deleted {deleted_count} vectors")
        return deleted_count
