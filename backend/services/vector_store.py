import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from backend.config import settings
from backend.services.text_splitter import DocumentChunk

logger = logging.getLogger(__name__)

class VectorStore:
    """
    FAISS-based vector database supporting:
    - Cosine similarity search using IndexFlatIP on normalized vectors
    - Persistent disk storage and automatic reload on startup
    - Document-level filtering (single document or cross-document search)
    - Full document deletion with index synchronization
    - Preserves exact page numbers and chunk metadata
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = Path(storage_dir or settings.VECTOR_DB_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.storage_dir / "faiss.index"
        self.metadata_file = self.storage_dir / "chunks_metadata.json"
        self.embeddings_file = self.storage_dir / "embeddings.npy"

        self.dimension = 384  # Matches all-MiniLM-L6-v2
        self.index = None
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings_matrix: Optional[np.ndarray] = None

        self._load_from_disk()

    def _init_empty_index(self):
        """Initializes a new empty FAISS IndexFlatIP (Inner Product = Cosine on unit vectors)."""
        import faiss
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []
        self.embeddings_matrix = np.empty((0, self.dimension), dtype=np.float32)

    def _load_from_disk(self):
        """Loads index and metadata from disk if present."""
        import faiss
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                
                if self.embeddings_file.exists():
                    self.embeddings_matrix = np.load(str(self.embeddings_file))
                else:
                    self.embeddings_matrix = np.empty((len(self.chunks), self.dimension), dtype=np.float32)

                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors from disk.")
                return
            except Exception as e:
                logger.error(f"Error loading FAISS index from disk: {e}. Reinitializing empty index.")

        self._init_empty_index()

    def save_to_disk(self):
        """Persists FAISS index, metadata, and embeddings matrix to disk."""
        import faiss
        try:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)

            if self.embeddings_matrix is not None:
                np.save(str(self.embeddings_file), self.embeddings_matrix)
            logger.info("Saved FAISS index and metadata to disk.")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: np.ndarray):
        """
        Adds document chunks and their corresponding normalized embeddings to the FAISS index.
        """
        if len(chunks) == 0:
            return

        if self.index is None:
            self._init_empty_index()

        embeddings_f32 = embeddings.astype(np.float32)

        # Add to FAISS index
        self.index.add(embeddings_f32)

        # Store metadata
        for chunk in chunks:
            self.chunks.append(chunk.to_dict())

        # Keep embeddings matrix for instant rebuilding on deletion
        if self.embeddings_matrix is None or len(self.embeddings_matrix) == 0:
            self.embeddings_matrix = embeddings_f32
        else:
            self.embeddings_matrix = np.vstack([self.embeddings_matrix, embeddings_f32])

        self.save_to_disk()

    def similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        document_id: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Performs cosine similarity search.
        If document_id is provided, filters results to that specific PDF.
        Returns list of chunk dicts enriched with 'score'.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Ensure query is 2D float32
        q_emb = query_embedding.reshape(1, -1).astype(np.float32)

        # Retrieve more candidates if document filtering is required
        search_k = min(self.index.ntotal, top_k * 4 if document_id else top_k)
        scores, indices = self.index.search(q_emb, search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.chunks):
                continue
            if score < min_score:
                continue

            chunk_meta = dict(self.chunks[idx])
            chunk_meta["score"] = float(score)

            if document_id and chunk_meta.get("document_id") != document_id:
                continue

            results.append(chunk_meta)
            if len(results) >= top_k:
                break

        return results

    def delete_document(self, document_id: str) -> int:
        """
        Deletes all chunks belonging to a document and rebuilds the FAISS index.
        Returns the number of chunks deleted.
        """
        if not self.chunks:
            return 0

        keep_indices = []
        deleted_count = 0
        new_chunks = []

        for i, chunk in enumerate(self.chunks):
            if chunk.get("document_id") == document_id:
                deleted_count += 1
            else:
                keep_indices.append(i)
                new_chunks.append(chunk)

        if deleted_count == 0:
            return 0

        # Rebuild index
        self._init_empty_index()
        if keep_indices and self.embeddings_matrix is not None and len(self.embeddings_matrix) > 0:
            new_embeddings = self.embeddings_matrix[keep_indices]
            self.index.add(new_embeddings)
            self.chunks = new_chunks
            self.embeddings_matrix = new_embeddings
        else:
            self.chunks = []
            self.embeddings_matrix = np.empty((0, self.dimension), dtype=np.float32)

        self.save_to_disk()
        return deleted_count

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Returns all chunks belonging to a document (e.g. for complete summarization)."""
        return [c for c in self.chunks if c.get("document_id") == document_id]

    def get_stats(self) -> Dict[str, Any]:
        """Returns index diagnostics."""
        unique_docs = set(c.get("document_id") for c in self.chunks)
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_chunks": len(self.chunks),
            "unique_documents": len(unique_docs)
        }

# Singleton instance
vector_store = VectorStore()
