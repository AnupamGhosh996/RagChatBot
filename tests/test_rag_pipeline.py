"""
Comprehensive automated tests for the PDF Intelligence RAG pipeline:
1. PDF extraction test
2. Chunking & metadata preservation test
3. Sentence Transformer embedding & FAISS vector search test
4. End-to-end RAG answer & citation generation test
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from tests.create_sample_pdf import create_sample_pdf
from backend.services.pdf_processor import pdf_processor
from backend.services.text_splitter import text_splitter_service
from backend.services.embedding_service import embedding_service
from backend.services.vector_store import vector_store
from backend.services.rag_pipeline import rag_pipeline

def run_tests():
    print("=" * 60)
    print("PDF Intelligence RAG Pipeline Verification Test")
    print("=" * 60)

    # Step 1: Create a verified test PDF
    pdf_path = root_dir / "tests" / "test_os_notes.pdf"
    print(f"\n[Step 1] Creating test PDF at {pdf_path}...")
    create_sample_pdf(str(pdf_path))
    assert pdf_path.exists(), "PDF creation failed!"
    print("  ✓ Test PDF created successfully.")

    # Step 2: Extract text page-by-page
    print("\n[Step 2] Testing PDF extraction and page numbering...")
    pages = pdf_processor.extract_pages(pdf_path)
    print(f"  ✓ Extracted {len(pages)} pages.")
    assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"

    for p in pages:
        print(f"    - Page {p['page_number']}: {p['char_count']} chars extracted.")
        assert p['char_count'] > 0, f"Page {p['page_number']} has 0 characters!"
    
    # Check that specific terms appear on their corresponding pages
    assert "kernel" in pages[0]["text"].lower(), "Page 1 should mention kernel architecture"
    assert "tlb" in pages[1]["text"].lower() or "paging" in pages[1]["text"].lower(), "Page 2 should mention paging/TLB"
    assert "deadlock" in pages[2]["text"].lower(), "Page 3 should mention deadlock"
    print("  ✓ Page text verification passed.")

    # Step 3: Test text chunking
    print("\n[Step 3] Testing RecursiveCharacterTextSplitter chunking...")
    doc_id = "test-doc-123"
    doc_name = "test_os_notes.pdf"
    chunks = text_splitter_service.split_document(doc_id, doc_name, pages)
    print(f"  ✓ Created {len(chunks)} chunks.")
    assert len(chunks) >= 3, "Expected at least 1 chunk per page"

    # Verify chunk metadata integrity
    for chunk in chunks:
        assert chunk.document_id == doc_id
        assert chunk.document_name == doc_name
        assert 1 <= chunk.page_number <= 3
        assert len(chunk.text) > 0
    print("  ✓ Chunk metadata and page mapping verified.")

    # Step 4: Test Embedding generation & FAISS storage
    print("\n[Step 4] Testing Embedding Generation (all-MiniLM-L6-v2) & FAISS...")
    texts = [c.text for c in chunks]
    embeddings = embedding_service.embed_texts(texts)
    print(f"  ✓ Generated embeddings shape: {embeddings.shape} (Dimension = {embeddings.shape[1]})")
    assert embeddings.shape[0] == len(chunks)
    assert embeddings.shape[1] == 384, f"Expected 384 dimensions, got {embeddings.shape[1]}"

    # Add to FAISS
    vector_store.add_chunks(chunks, embeddings)
    stats = vector_store.get_stats()
    print(f"  ✓ FAISS Index contains {stats['total_vectors']} vectors.")
    assert stats['total_vectors'] >= len(chunks)

    # Step 5: Test Similarity Search
    print("\n[Step 5] Testing Similarity Search & Context Retrieval...")
    test_queries = [
        ("What is a Translation Lookaside Buffer and how does paging work?", 2), # Expect Page 2
        ("What are the 4 conditions necessary for a deadlock?", 3),            # Expect Page 3
        ("What is the difference between a monolithic kernel and microkernel?", 1), # Expect Page 1
    ]

    for question, expected_page in test_queries:
        print(f"\n  Query: '{question}'")
        q_emb = embedding_service.embed_query(question)
        matches = vector_store.similarity_search(q_emb, top_k=3)
        assert len(matches) > 0, "No matches returned!"

        top_match = matches[0]
        print(f"    -> Top Result: Document '{top_match['document_name']}', Page {top_match['page_number']}, Score: {top_match['score']:.4f}")
        print(f"    -> Snippet: {top_match['text'][:120]}...")

        # Check if the expected page is in the top 2 results
        retrieved_pages = [m['page_number'] for m in matches[:2]]
        assert expected_page in retrieved_pages, f"Expected page {expected_page} in top 2 retrieved pages, got {retrieved_pages}"
        print(f"    ✓ Page {expected_page} accurately retrieved!")

    # Step 6: Test RAG Pipeline end-to-end
    print("\n[Step 6] Testing End-to-End RAG Pipeline with Citations...")
    response = rag_pipeline.answer_question(
        question="What is the role of an operating system and how does a microkernel differ from a monolithic kernel?",
        conversation_id="test-conv"
    )
    print(f"  Answer preview:\n  {response.answer[:250]}...\n")
    print(f"  Citations ({len(response.citations)}):")
    for cit in response.citations:
        print(f"    - [{cit.document_name}, Page {cit.page_number}]: {cit.snippet[:90]}...")
    
    assert len(response.citations) > 0, "Expected at least one citation"
    assert any(c.page_number == 1 for c in response.citations), "Expected Page 1 citation for kernel question"
    print("  ✓ Citations accurately mapped to Page 1.")

    print("\n" + "=" * 60)
    print("ALL RAG PIPELINE TESTS PASSED SUCCESSFULLY! ✓")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
