from typing import List, Optional
from pydantic import BaseModel, Field
import datetime

class DocumentInfo(BaseModel):
    id: str = Field(..., description="Unique document UUID")
    filename: str = Field(..., description="Stored filename")
    original_name: str = Field(..., description="Original uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    file_size_formatted: str = Field(..., description="Human readable file size e.g. 1.2 MB")
    page_count: int = Field(..., description="Total pages in the PDF")
    chunk_count: int = Field(..., description="Number of text chunks generated")
    upload_timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    download_url: Optional[str] = None

class UploadResponse(BaseModel):
    success: bool
    message: str
    documents: List[DocumentInfo]

class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    snippet: str
    score: Optional[float] = None

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    document_id: Optional[str] = None  # None means search all documents

class ChatResponse(BaseModel):
    conversation_id: str
    question: str
    answer: str
    citations: List[Citation]
    retrieved_chunks_count: int

class ConversationMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    citations: Optional[List[Citation]] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[ConversationMessage]

class DocumentSummaryRequest(BaseModel):
    document_id: str

class DocumentSummaryResponse(BaseModel):
    document_id: str
    document_name: str
    summary: str
    key_points: List[str]
    page_count: int

class HealthResponse(BaseModel):
    status: str
    documents_count: int
    vectors_count: int
    claude_configured: bool
    embedding_model: str
