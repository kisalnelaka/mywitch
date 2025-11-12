# 📚 PDF Learning Assistant

An AI-powered local knowledge assistant that lets you upload PDFs, index their content, and ask natural-language questions about them.

Built using **FastAPI**, **Streamlit**, **LangChain**, **Chroma**, and **Ollama**, this system combines document retrieval and local LLM reasoning to create a fully self-contained learning environment that runs entirely on your machine — no external APIs required.

---

## 🚀 Features

### 🔍 Intelligent Document Understanding
- Upload one or multiple PDF files directly via the Streamlit dashboard
- Text is extracted using PyPDF2 and chunked intelligently
- Embeddings created using Sentence-Transformers (`all-MiniLM-L6-v2`)
- Stored persistently in a Chroma vector database for fast semantic retrieval
- Metadata (source file, page number, ingestion timestamp) preserved with each chunk

### 💬 Ask & Learn
- Query your indexed PDFs in natural language
- Uses Retrieval-Augmented Generation (RAG):
  - Retrieves the most relevant document chunks (configurable k)
  - Sends them to a local Ollama LLM (e.g., Mistral, Llama 3) for context-aware responses
  - Displays the answer, source filenames, and page previews with full transparency
- Adjustable retriever depth (k parameter) to control retrieval depth

### 📊 Dashboard & Metrics
- **Interactive Streamlit dashboard** with three main tabs:
  - **Upload / Ingest**: Add new PDFs, rebuild the entire index, or wipe and start fresh
  - **Ask / Chat**: Query your knowledge base with adjustable retrieval depth
  - **Metrics**: View query logs, ingest history, and system status
- All metrics stored in **SQLite** for persistence (`/data/db.sqlite`)
- Recent queries and ingests displayed with timestamps and latency metrics

---

## 🧩 Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Interactive Python UI for upload/chat/metrics |
| **Backend** | FastAPI | REST API for ingestion, querying, and metrics |
| **Vector Database** | Chroma | Store and retrieve embeddings with metadata |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) | Local vector embeddings |
| **LLM** | Ollama | Local language model reasoning (Mistral, Llama 3, etc.) |
| **Metrics DB** | SQLite | Store query logs and ingest history |
| **Deployment** | Docker Compose | Fully containerized setup |

---

## 🐳 Quick Start (Docker)

### Prerequisites
- **Docker & Docker Compose** installed
- **Ollama** installed and running on your host
- A model pulled in Ollama (e.g., Mistral)

### Setup & Run

1. **Start Ollama** (on your host machine):
```bash
ollama serve  # or: sudo systemctl start ollama
ollama pull mistral
```

2. **Clone and navigate to the project**:
```bash
git clone https://github.com/kisalnelaka/mywitch.git
cd mywitch
```

3. **Build and run with Docker Compose**:
```bash
docker compose up --build
```

4. **Access the dashboard**:
- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API docs (Swagger)**: http://localhost:8000/docs

5. **Upload & Index PDFs**:
   - Go to the "Upload / Ingest" tab
   - Select a PDF and click "Upload & Index"
   - Your data is stored under `./data/` (persistent between restarts)

---

## 🧠 How It Works

### 1. Upload PDF
- FastAPI receives the file → saves under `/data/uploads/`
- PDF text is extracted via PyPDF2 with page tracking

### 2. Chunking & Embedding
- Text split into overlapping chunks (1000 chars, 200 overlap) using RecursiveCharacterTextSplitter
- Each chunk embedded into a vector using SentenceTransformers
- Metadata attached: source filename, page number, ingestion timestamp

### 3. Vector Storage
- Embeddings + metadata saved in Chroma (persistent directory: `/data/chroma`)
- Enables fast semantic search across all documents

### 4. Querying
- Input question is embedded using the same model
- Semantic retrieval fetches top k chunks most similar to the query
- Retrieved text fed into Ollama model → generates grounded, contextual answer
- Sources and page previews returned for transparency

### 5. Metrics & Logging
- Query latency, questions, and ingestion events logged to SQLite
- Metrics dashboard displays recent queries, ingests, and system status

---

## 📂 Directory Structure

```
mywitch/
├── docker-compose.yml          # Service orchestration
├── LICENSE                      # MIT License
├── README.md                    # This file
├── backend/
│   ├── app.py                  # FastAPI application & endpoints
│   ├── rag.py                  # RAG pipeline (embedding, chunking, QA)
│   ├── db.py                   # SQLAlchemy models & database setup
│   ├── utils.py                # Text splitting utilities
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Backend container image
├── frontend/
│   ├── app.py                  # Streamlit dashboard
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Frontend container image
├── data/
│   ├── chroma/                 # Vector embeddings (persisted)
│   ├── uploads/                # Uploaded PDFs (persisted)
│   └── db.sqlite               # Metrics and logs database
└── ollama/                      # (empty) Ollama integration docs
```

---

## 🔌 API Endpoints

### Backend FastAPI (`http://localhost:8000`)

#### Health Check
```
GET /
```
Returns: `{"status": "ok", "message": "Backend is running!"}`

#### Upload & Index PDF
```
POST /upload_pdf/
Body: multipart form with 'file' (PDF)
Returns: {"filename": str, "chunks_indexed": int}
```

#### Ask a Question
```
POST /ask/
Body: form data with 'question' (string) and 'k' (int, default 4)
Returns: {"answer": str, "sources": List[{source, page, preview}], "latency": float}
```

#### Reindex All PDFs
```
POST /reindex_all/
Returns: {"status": "ok", "total_chunks": int}
```

#### Get Metrics
```
GET /metrics/
Returns: {
  "queries_total": int,
  "recent_queries": List[{question, latency, ts}],
  "recent_ingests": List[{filename, chunks, ts}],
  "chroma_exists": bool,
  "uploads_dir": str
}
```

#### Wipe Index
```
DELETE /wipe_index/
Returns: {"status": "ok", "message": "Index wiped. Reindex to rebuild."}
```

---

## 🧰 Tech Stack & Dependencies

### Backend (`backend/requirements.txt`)
- **FastAPI** + **Uvicorn** — Web framework & ASGI server
- **PyPDF2** — PDF text extraction
- **LangChain** (core, community, text-splitters, ollama) — RAG orchestration
- **Chroma** — Vector database
- **SentenceTransformers** — Local embeddings
- **SQLAlchemy** — ORM for metrics storage
- **Pandas** — Data manipulation

### Frontend (`frontend/requirements.txt`)
- **Streamlit** — Interactive web UI
- **Requests** — HTTP client for backend communication
- **Pandas** — Data display

### Environment Configuration
Set via Docker Compose or `.env`:
- `OLLAMA_HOST` — Ollama server URL (default: `http://host.docker.internal:11434`)
- `OLLAMA_MODEL` — Model name (default: `mistral`)
- `CHROMA_DIR` — Vector database path (default: `/data/chroma`)
- `DB_PATH` — SQLite database path (default: `/data/db.sqlite`)
- `UPLOAD_DIR` — PDF upload directory (default: `/data/uploads`)

---

## 📖 Example Workflow

1. **Upload documents**:
   - Go to "Upload / Ingest" tab
   - Upload your textbook, research papers, or documentation
   - System extracts text, chunks it, and creates embeddings

2. **Ask questions**:
   - Go to "Ask / Chat" tab
   - Type: *"What are the main concepts in Chapter 2?"*
   - Adjust retriever `k` (number of chunks to retrieve)
   - System retrieves relevant chunks and generates an answer

3. **Monitor**:
   - Go to "Metrics" tab
   - View query history, latency, ingest logs
   - Check storage and vector database status

---

## ⚠️ Limitations

- **PDF extraction quality** depends on PDF formatting — scanned or image-based PDFs require OCR (not yet implemented)
- **Context length limits** — large answers may truncate depending on the LLM's context window
- **No fine-tuning** — uses RAG instead of permanently modifying the model's weights
- **Local-only inference** — Ollama must be running on the same machine (or network-accessible)
- **No authentication** — for personal/local use only; not multi-user safe
- **Not cloud-scaled** — intended for individual study/research, not production environments

---

## 🛠️ Planned Enhancements

- ✅ OCR support for scanned PDFs
- ✅ Document deletion / re-ingestion controls
- ✅ Multi-user dashboard with authentication
- ✅ GPU usage visualization and control
- ✅ Reranker for better retrieval accuracy
- ✅ Export chat and metrics history
- ✅ Support for multiple document formats (DOCX, TXT, Markdown)

---

## 🤝 Contributing

Pull requests and ideas are welcome! To contribute:

```bash
git clone https://github.com/kisalnelaka/mywitch.git
cd mywitch
# Make your changes and submit a PR
```

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
Feel free to use, modify, and distribute.
 PDF Learning Assistant (RAG + Ollama + Chroma)