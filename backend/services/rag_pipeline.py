import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple

from backend.config import settings
from backend.services.embedding_service import embedding_service
from backend.services.vector_store import vector_store
from backend.services.llm_service import llm_service
from backend.models.schemas import Citation, ChatResponse

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Coordinates the full Retrieval-Augmented Generation pipeline:
    1. Query embedding via Sentence Transformers
    2. Vector similarity search in FAISS
    3. Multi-source context assembly & citation extraction
    4. Grounded answer generation via Anthropic Claude
    5. Multi-turn conversation memory
    """

    def __init__(self):
        # In-memory storage for active conversations: {conversation_id: [messages...]}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}

    def get_or_create_conversation_id(self, conv_id: Optional[str]) -> str:
        if not conv_id:
            conv_id = str(uuid.uuid4())
        if conv_id not in self.conversations:
            self.conversations[conv_id] = []
        return conv_id

    def get_conversation_history(self, conv_id: str) -> List[Dict[str, Any]]:
        return self.conversations.get(conv_id, [])

    def clear_conversation(self, conv_id: str) -> bool:
        if conv_id in self.conversations:
            self.conversations[conv_id] = []
            return True
        return False

    def build_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        """
        Builds structured, deduplicated citations with page references and text snippets.
        """
        citations: List[Citation] = []
        seen = set()

        for chunk in chunks:
            doc_id = chunk.get("document_id", "")
            page_num = chunk.get("page_number", 1)
            chunk_id = chunk.get("chunk_id", "")
            doc_name = chunk.get("document_name", "Unknown Document")
            text = chunk.get("text", "")
            score = chunk.get("score")

            # Avoid exact duplicate citations on same page with similar content
            key = (doc_id, page_num, chunk_id)
            if key in seen:
                continue
            seen.add(key)

            # Create an illustrative 180-char snippet
            clean_snippet = " ".join(text.split())
            if len(clean_snippet) > 200:
                clean_snippet = clean_snippet[:197] + "..."

            citations.append(
                Citation(
                    document_id=doc_id,
                    document_name=doc_name,
                    page_number=page_num,
                    chunk_id=chunk_id,
                    snippet=clean_snippet,
                    score=score
                )
            )

        return citations

    def answer_question(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        document_id: Optional[str] = None,
        top_k: int = None
    ) -> ChatResponse:
        """
        Main query processing method:
        - Embeds the query
        - Retrieves top matching passages
        - Calls Claude LLM
        - Records conversation history
        """
        conv_id = self.get_or_create_conversation_id(conversation_id)
        k = top_k or settings.TOP_K_CHUNKS

        # 1. Embed query
        query_embedding = embedding_service.embed_query(question)

        # 2. Search FAISS index
        retrieved_chunks = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=k,
            document_id=document_id,
            min_score=settings.SIMILARITY_THRESHOLD
        )

        # If strict threshold yielded nothing, try relaxed threshold if index has chunks
        if not retrieved_chunks and vector_store.index and vector_store.index.ntotal > 0:
            retrieved_chunks = vector_store.similarity_search(
                query_embedding=query_embedding,
                top_k=k,
                document_id=document_id,
                min_score=0.1
            )

        # 3. Build Citations
        citations = self.build_citations(retrieved_chunks)

        # 4. Check if any documents exist at all
        if not retrieved_chunks and (vector_store.index is None or vector_store.index.ntotal == 0):
            answer = (
                "No documents have been uploaded yet. Please upload one or more PDF files "
                "using the sidebar or the upload area before asking questions."
            )
            citations = []
            return ChatResponse(
                conversation_id=conv_id,
                question=question,
                answer=answer,
                citations=citations,
                retrieved_chunks_count=0
            )

        # 5. Generate Answer via Claude
        history = self.conversations[conv_id]
        
        if llm_service.is_configured():
            try:
                answer = llm_service.generate_rag_answer(
                    question=question,
                    retrieved_chunks=retrieved_chunks,
                    conversation_history=history
                )
            except Exception as e:
                logger.error(f"Claude execution failed: {e}")
                answer = f"Error generating answer with Claude: {str(e)}"
        else:
            # Helpful fallback when API key is not yet set
            context_summary = "\n".join(
                f"- [{c.document_name}, Page {c.page_number}]: {c.snippet}"
                for c in citations
            )
            answer = (
                "⚠️ **Anthropic Claude API Key is not configured.**\n\n"
                "To enable Claude responses, add your Anthropic API key to `backend/.env`:\n"
                "```env\nANTHROPIC_API_KEY=sk-ant-...\n```\n\n"
                f"**Top Retrieved Context Passages ({len(citations)}):**\n"
                f"{context_summary}"
            )

        # 6. Save to conversation history
        self.conversations[conv_id].append({
            "role": "user",
            "content": question
        })
        self.conversations[conv_id].append({
            "role": "assistant",
            "content": answer,
            "citations": [c.model_dump() for c in citations]
        })

        return ChatResponse(
            conversation_id=conv_id,
            question=question,
            answer=answer,
            citations=citations,
            retrieved_chunks_count=len(retrieved_chunks)
        )

# Singleton instance
rag_pipeline = RAGPipeline()
