import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.routes.upload import router as upload_router, load_catalog
from backend.routes.chat import router as chat_router
from backend.services.vector_store import vector_store
from backend.services.llm_service import llm_service
from backend.models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pdf_intelligence")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting PDF Intelligence RAG backend...")
    logger.info(f"Storage dir: {settings.UPLOAD_DIR}")
    logger.info(f"Vector DB dir: {settings.VECTOR_DB_DIR}")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL_NAME}")
    logger.info(f"Claude API Key configured: {llm_service.is_configured()}")
    yield
    # Shutdown actions
    logger.info("Shutting down PDF Intelligence RAG backend...")

app = FastAPI(
    title="PDF Intelligence RAG API",
    description="Retrieval-Augmented Generation (RAG) backend for PDF question answering using LangChain, SentenceTransformers, FAISS, and Anthropic Claude.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload_router)
app.include_router(chat_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "PDF Intelligence RAG API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Returns backend operational status, vector store statistics, and LLM configuration."""
    catalog = load_catalog()
    stats = vector_store.get_stats()
    
    return HealthResponse(
        status="healthy",
        documents_count=len(catalog),
        vectors_count=stats.get("total_vectors", 0),
        claude_configured=llm_service.is_configured(),
        embedding_model=settings.EMBEDDING_MODEL_NAME
    )

# Global exception handler for uncaught server errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check server logs for details."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
