import logging
from typing import List
from fastapi import APIRouter, HTTPException, status

from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse,
    ConversationHistoryResponse,
    ConversationMessage
)
from backend.services.rag_pipeline import rag_pipeline
from backend.services.vector_store import vector_store
from backend.services.llm_service import llm_service
from backend.routes.upload import load_catalog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat & Intelligence"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask a question against indexed PDFs:
    - Generates query embedding
    - Retrieves top 4-5 relevant chunks from FAISS
    - Prompts Anthropic Claude with retrieved context and strict rules
    - Returns answer with precise document and page number citations
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    try:
        response = rag_pipeline.answer_question(
            question=request.question.strip(),
            conversation_id=request.conversation_id,
            document_id=request.document_id
        )
        return response
    except Exception as e:
        logger.error(f"Chat execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering your question: {str(e)}"
        )

@router.post("/summary", response_model=DocumentSummaryResponse)
async def summarize_document(request: DocumentSummaryRequest):
    """
    Generates an executive summary and key takeaways for an entire PDF.
    """
    catalog = load_catalog()
    doc = next((d for d in catalog if d.get("id") == request.document_id), None)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{request.document_id}' not found."
        )

    chunks = vector_store.get_document_chunks(request.document_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexed content found for this document."
        )

    if not llm_service.is_configured():
        return DocumentSummaryResponse(
            document_id=request.document_id,
            document_name=doc.get("original_name", "Document"),
            summary="Claude API key is not configured. Please set ANTHROPIC_API_KEY in backend/.env to generate intelligent summaries.",
            key_points=[
                f"Document has {doc.get('page_count', 0)} pages.",
                f"Split into {len(chunks)} searchable chunks.",
                "Configure your Claude API key to unlock automated executive summaries."
            ],
            page_count=doc.get("page_count", 0)
        )

    try:
        summary_text, key_points = llm_service.generate_document_summary(
            document_name=doc.get("original_name", "Document"),
            all_chunks=chunks
        )
        return DocumentSummaryResponse(
            document_id=request.document_id,
            document_name=doc.get("original_name", "Document"),
            summary=summary_text,
            key_points=key_points,
            page_count=doc.get("page_count", 0)
        )
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )

@router.get("/history/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_history(conversation_id: str):
    """Retrieves message history for a conversation."""
    history = rag_pipeline.get_conversation_history(conversation_id)
    messages = [ConversationMessage(**msg) for msg in history]
    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        messages=messages
    )

@router.delete("/history/{conversation_id}")
async def clear_history(conversation_id: str):
    """Clears conversation memory."""
    success = rag_pipeline.clear_conversation(conversation_id)
    return {"success": success, "message": "Conversation cleared."}
