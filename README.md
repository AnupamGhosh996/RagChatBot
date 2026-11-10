# PDF Intelligence – RAG-Based Question Answering Application

A modern, production-grade **Retrieval-Augmented Generation (RAG)** web application that enables users to upload PDF documents, extract and chunk text with exact page-level citations, generate dense vector embeddings, and interact with an intelligent document assistant powered by **Anthropic Claude** and **FAISS**.

---

## 1. System Architecture & RAG Pipeline

### How the Pipeline Works:

1. **PDF Upload & Validation**:
   - Accepts single or multiple PDF documents via drag-and-drop or file selector.
   - Validates MIME type and file size (up to 50MB).
2. **Text Extraction & Cleaning**:
   - Uses **PyMuPDF (`fitz`)** (with **`pypdf`** fallback) to extract clean text from every page.
   - Cleans formatting, resolves hyphenated word splits across line breaks, and preserves exact 1-indexed page numbers.
3. **Recursive Chunking**:
   - Uses LangChain's `RecursiveCharacterTextSplitter` configured for ~1000 characters per chunk with ~200 character overlap.
   - Associates every chunk with explicit metadata: `document_id`, `document_name`, `page_number`, and `chunk_id`.
4. **Embedding Generation**:
   - Computes 384-dimensional dense vector embeddings using Hugging Face's `all-MiniLM-L6-v2`.
   - Normalizes embeddings to unit length for cosine similarity.
5. **FAISS Vector Indexing**:
   - Stores vectors in an `IndexFlatIP` index with persistent disk storage.
   - Supports cross-document search or scoping to a specific selected PDF.
6. **Query Processing & Retrieval**:
   - Embeds user questions with the same model.
   - Retrieves top 4–5 most relevant chunks using cosine similarity.
7. **Claude Generation & Citation Grounding**:
   - Injects retrieved passages formatted in untrusted `<context>` blocks into Anthropic's Claude API.
   - Strictly enforces the 10 Grounding Rules (no hallucinations, explicit page citations, defense against prompt injections embedded in PDF text).
8. **Interactive Citations & PDF Viewer**:
   - Citations show document title, page number, and text excerpt.
   - Clicking any citation jumps directly to that specific page in the built-in PDF viewer (`#page=N`).

---

## 2. Project Directory Structure

```
RAG app/
├── backend/
│   ├── main.py                     # FastAPI application entrypoint & CORS
│   ├── config.py                   # Environment settings & directory resolver
│   ├── requirements.txt            # Python backend dependencies
│   ├── .env.example                # Template for environment variables
│   ├── .env                        # Local environment configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic schemas (Chat, Citations, Documents)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py        # PyMuPDF text extraction & formatting cleaner
│   │   ├── text_splitter.py       # RecursiveCharacterTextSplitter with page preservation
│   │   ├── embedding_service.py    # SentenceTransformers all-MiniLM-L6-v2
│   │   ├── vector_store.py         # FAISS IndexFlatIP & metadata persistence
│   │   ├── llm_service.py          # Anthropic Claude API official Python SDK
│   │   └── rag_pipeline.py         # End-to-end RAG orchestrator & memory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── upload.py               # Document upload, listing, deletion, file streaming
│   │   └── chat.py                 # Question answering, document summary, history
│   └── storage/
│       ├── uploads/                # Physical PDF files directory
│       └── vector_db/              # FAISS index and chunk metadata files
├── frontend/
│   ├── package.json                # React & Vite dependencies
│   ├── vite.config.js              # Vite server configuration & API proxy
│   ├── tailwind.config.js          # Tailwind CSS styling configuration
│   ├── postcss.config.js
│   ├── index.html                  # HTML entrypoint
│   └── src/
│       ├── main.jsx                # React root mount
│       ├── App.jsx                 # Main stateful application component
│       ├── index.css               # Global styling, scrollbars & markdown theme
│       ├── services/
│       │   └── api.js              # Axios REST API client
│       └── components/
│           ├── Sidebar.jsx         # Document manager, scoping, export & status
│           ├── ChatWindow.jsx      # Message list, prompts, auto-expanding input
│           ├── MessageBubble.jsx   # Formatted markdown messages & citations
│           ├── FileUpload.jsx      # Drag-and-drop uploader with live step indicators
│           ├── SourceCitation.jsx  # Clickable citation pill with excerpt drawer
│           └── PDFViewer.jsx       # Built-in document viewer with page jump
├── tests/
│   ├── create_sample_pdf.py        # Dependency-free 3-page test PDF generator
│   └── test_rag_pipeline.py        # End-to-end automated verification script
├── package.json                    # Workspace root scripts
├── requirements.txt                # Root requirements pointer
├── .env.example                    # Root environment template
└── README.md                       # Comprehensive documentation
```

---

## 3. Technology Stack

### Frontend
- **React.js 18** with **Vite**: Ultra-fast build tool and reactive component model.
- **Tailwind CSS**: Modern ChatGPT/Linear/Claude-inspired design system with subtle borders and dark theme.
- **Lucide React**: Clean vector icon suite.
- **Axios**: HTTP client with upload progress hooks.

### Backend
- **Python 3.10+ / 3.11+ / 3.12+**
- **FastAPI**: Asynchronous high-performance REST framework.
- **Uvicorn**: Lightning-fast ASGI production server.
- **Pydantic v2**: Type enforcement and payload validation.

### RAG & PDF Processing
- **LangChain**: Text splitting via `RecursiveCharacterTextSplitter`.
- **PyMuPDF (`fitz`)** & **`pypdf`**: High-fidelity text extraction with exact page index mapping.
- **Sentence Transformers (`all-MiniLM-L6-v2`)**: 384-dimensional dense semantic representations.
- **FAISS (`faiss-cpu`)**: Exact inner-product (cosine similarity) vector index.
- **Anthropic Claude API**: Official `anthropic` Python SDK utilizing `claude-3-5-sonnet-20241022`.

---

## 4. Setup and Installation Instructions

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- An Anthropic Claude API Key ([Anthropic Console](https://console.anthropic.com/))

---

### Step 1: Backend Setup

1. Open your terminal in the project root:
   ```bash
   cd "RAG app/backend"
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your `.env` file:
   ```bash
   # Copy the example environment file
   copy .env.example .env     # On Windows
   cp .env.example .env       # On Linux/macOS
   ```

---

### Step 2: Configure Your Anthropic Claude API Key

1. Sign up or log in to the [Anthropic Console](https://console.anthropic.com/).
2. Navigate to **API Keys** -> **Create Key**.
3. Copy your API key (starts with `sk-ant-...`).
4. Open `backend/.env` in your text editor and set:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
   ```

*(Note: If you run without an API key initially, the application will still extract text, chunk, embed, and search FAISS; it will display the retrieved citations along with a notification to insert your key).*

---

### Step 3: Frontend Setup

1. In a new terminal window, navigate to the `frontend` folder:
   ```bash
   cd "RAG app/frontend"
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

---

## 5. Running the Application

### Start the Backend Server
From `RAG app/backend` (with virtual environment activated):
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
- API will be live at: `http://localhost:8000`
- Interactive Swagger docs at: `http://localhost:8000/docs`

### Start the Frontend Application
From `RAG app/frontend`:
```bash
npm run dev
```
- Web interface will open at: `http://localhost:5173`

---

## 6. Verifying the Pipeline (Automated Test Suite)

To test the entire pipeline (PDF generation, text extraction, chunking, embedding generation, FAISS indexing, similarity retrieval, and citation verification) in under 10 seconds:

```bash
# From project root:
python tests/test_rag_pipeline.py
```

### What this test verifies:
- Creates a 3-page test PDF (`tests/test_os_notes.pdf`) covering Operating Systems, Virtual Memory, and Deadlocks.
- Confirms page-by-page extraction accuracy.
- Confirms `RecursiveCharacterTextSplitter` correctly maps chunks to their originating pages.
- Verifies `all-MiniLM-L6-v2` generates 384-dimensional embeddings.
- Executes similarity queries for concepts on Page 1, Page 2, and Page 3, ensuring top similarity search results match the exact expected page numbers!

---

## 7. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Upload one or multiple PDFs, extract text, chunk, embed, and index in FAISS. |
| `GET` | `/api/documents` | List all uploaded documents with metadata (pages, chunks, sizes). |
| `DELETE` | `/api/documents/{id}` | Delete a document, remove its physical file, and prune vectors from FAISS. |
| `GET` | `/api/documents/{id}/file` | Stream PDF directly to the browser viewer for page jumps. |
| `POST` | `/api/chat` | Submit question with conversation memory; returns answer & source citations. |
| `POST` | `/api/summary` | Generate executive summary and key takeaways for an entire PDF. |
| `GET` | `/api/history/{id}` | Retrieve conversation history for a given conversation ID. |
| `DELETE` | `/api/history/{id}` | Clear conversation memory. |
| `GET` | `/api/health` | Backend status, total indexed vector count, and Claude configuration status. |

---

## 8. Intelligent Answering Rules & Untrusted Input Defense

The LLM is governed by strict system instructions to guarantee truthful, grounded document intelligence:

1. **Grounded Answers**: Answers are derived strictly from retrieved context passages.
2. **Zero Hallucination**: Does not fabricate facts or page numbers.
3. **Out-of-Scope Fallback**: Clearly states if information is missing from the document.
4. **Exact Page Citations**: Every factual statement is backed by document and page number.
5. **Untrusted Data Isolation**: Document contents are encapsulated in `<context>` XML blocks and treated as untrusted data, preventing prompt injection attacks hidden inside uploaded PDFs.
6. **Multi-turn Memory**: Maintains context for follow-up questions within the active chat session.
7. **Document Summarization**: Provides automated executive summaries with structured key takeaways.

---

## 9. Key UI Features

- **Document Scoping**: Click any document in the sidebar to scope questions exclusively to that file, or select "Search All Documents" to query across all uploaded PDFs.
- **Clickable Citations**: Click any citation pill (`Document.pdf (Page 2)`) to open the built-in PDF viewer and navigate directly to that page.
- **Quick Prompts**: One-click suggested questions (*Summarize*, *Important Topics*, *Explain Concepts*, *Exam Questions*).
- **Export Chat**: Export your entire conversation with formatted markdown citations with one click.
- **File Management**: View file size, page count, chunk count, and delete documents with instant index re-sync.
