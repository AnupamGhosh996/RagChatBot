import os
import json
import uuid
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from backend.config import settings
from backend.models.schemas import DocumentInfo, UploadResponse
from backend.services.pdf_processor import pdf_processor, PDFProcessingError
from backend.services.text_splitter import text_splitter_service
from backend.services.embedding_service import embedding_service
from backend.services.vector_store import vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Documents"])

CATALOG_PATH = settings.UPLOAD_DIR / "documents_catalog.json"
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def format_file_size(size_bytes: int) -> str:
    """Format bytes into KB, MB, etc."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def load_catalog() -> List[dict]:
    if CATALOG_PATH.exists():
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_catalog(catalog: List[dict]):
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload one or multiple PDF documents:
    1. Validates file format and size
    2. Saves PDF securely to disk
    3. Extracts text page-by-page (PyMuPDF)
    4. Splits text into chunks with metadata
    5. Computes dense embeddings with SentenceTransformers
    6. Stores vectors and chunks in FAISS
    7. Updates document catalog
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    processed_docs: List[DocumentInfo] = []
    catalog = load_catalog()

    for file in files:
        original_name = file.filename or "unnamed.pdf"
        
        # 1. Validate file extension
        if not original_name.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{original_name}' is not a PDF. Only PDF files are supported."
            )

        # 2. Read content & validate size
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{original_name}' is empty (0 bytes)."
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{original_name}' exceeds the maximum allowed size of {MAX_FILE_SIZE_MB}MB."
            )

        doc_id = str(uuid.uuid4())
        safe_name = f"{doc_id}_{Path(original_name).name}"
        saved_file_path = settings.UPLOAD_DIR / safe_name

        try:
            # Save file to disk
            with open(saved_file_path, "wb") as f:
                f.write(content)

            # 3. Extract text page-by-page
            pages = pdf_processor.extract_pages(saved_file_path)
            page_count = len(pages)

            # 4. Chunk text while preserving page numbers
            chunks = text_splitter_service.split_document(
                document_id=doc_id,
                document_name=original_name,
                pages=pages
            )

            if not chunks:
                raise PDFProcessingError("No readable content found to generate chunks.")

            # 5. Generate embeddings
            texts_to_embed = [chunk.text for chunk in chunks]
            embeddings = embedding_service.embed_texts(texts_to_embed)

            # 6. Index in FAISS
            vector_store.add_chunks(chunks, embeddings)

            doc_info = DocumentInfo(
                id=doc_id,
                filename=safe_name,
                original_name=original_name,
                file_size=file_size,
                file_size_formatted=format_file_size(file_size),
                page_count=page_count,
                chunk_count=len(chunks),
                download_url=f"/api/documents/{doc_id}/file"
            )

            processed_docs.append(doc_info)
            catalog.append(doc_info.model_dump())

        except PDFProcessingError as ppe:
            # Clean up uploaded file if processing failed
            if saved_file_path.exists():
                saved_file_path.unlink()
            logger.error(f"PDF extraction error for {original_name}: {ppe}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not process '{original_name}': {str(ppe)}"
            )
        except Exception as e:
            if saved_file_path.exists():
                saved_file_path.unlink()
            logger.error(f"Unexpected upload failure: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process '{original_name}': {str(e)}"
            )

    save_catalog(catalog)

    return UploadResponse(
        success=True,
        message=f"Successfully processed {len(processed_docs)} document(s).",
        documents=processed_docs
    )

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """Returns the list of all indexed documents."""
    raw_catalog = load_catalog()
    return [DocumentInfo(**item) for item in raw_catalog]

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Deletes a document:
    - Removes it from the catalog
    - Removes its vectors and chunks from FAISS
    - Removes the uploaded PDF file from disk
    """
    catalog = load_catalog()
    doc_to_delete = None
    remaining_catalog = []

    for doc in catalog:
        if doc.get("id") == document_id:
            doc_to_delete = doc
        else:
            remaining_catalog.append(doc)

    if not doc_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    # Delete physical file
    file_path = settings.UPLOAD_DIR / doc_to_delete.get("filename", "")
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete physical file {file_path}: {e}")

    # Remove vectors from FAISS
    deleted_chunks = vector_store.delete_document(document_id)

    # Save updated catalog
    save_catalog(remaining_catalog)

    return {
        "success": True,
        "message": f"Document '{doc_to_delete.get('original_name')}' deleted successfully.",
        "deleted_chunks": deleted_chunks
    }

@router.get("/documents/{document_id}/file")
async def get_document_file(document_id: str):
    """
    Streams the original PDF file for browser viewing.
    Allows frontend PDFViewer to display pages directly.
    """
    catalog = load_catalog()
    doc = next((d for d in catalog if d.get("id") == document_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = settings.UPLOAD_DIR / doc.get("filename", "")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=doc.get("original_name", "document.pdf"),
        content_disposition_type="inline"
    )
