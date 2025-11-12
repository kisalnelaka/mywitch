import os, time, shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from rag import ingest_pdf, qa_answer, rebuild_from_uploads, UPLOAD_DIR, CHROMA_DIR
from db import init_db, get_session, QueryLog, IngestLog

app = FastAPI(title="PDF RAG Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure paths & DB
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)
init_db()

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend is running!"}

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Save to uploads, ingest into Chroma."""
    dst = os.path.join(UPLOAD_DIR, file.filename)
    with open(dst, "wb") as f:
        f.write(await file.read())

    chunks = ingest_pdf(dst)
    with get_session() as s:
        s.add(IngestLog(filename=file.filename, chunks=chunks))
        s.commit()
    return {"filename": file.filename, "chunks_indexed": chunks}

@app.post("/reindex_all/")
def reindex_all() -> Dict[str, Any]:
    total = rebuild_from_uploads()
    return {"status": "ok", "total_chunks": total}

@app.post("/ask/")
def ask(question: str = Form(...), k: int = Form(4)) -> Dict[str, Any]:
    t0 = time.time()
    out = qa_answer(question, k=k)
    latency = time.time() - t0

    with get_session() as s:
        s.add(QueryLog(question=question, latency=latency))
        s.commit()

    return {"answer": out["answer"], "sources": out["sources"], "latency": latency}

@app.get("/metrics/")
def metrics():
    from sqlalchemy import func, select
    with get_session() as s:
        qcount = s.scalar(select(func.count()).select_from(QueryLog)) or 0
        last5 = s.execute(
            select(QueryLog.question, QueryLog.latency, QueryLog.created_at)
            .order_by(QueryLog.id.desc())
            .limit(5)
        ).all()
        ings = s.execute(
            select(IngestLog.filename, IngestLog.chunks, IngestLog.created_at)
            .order_by(IngestLog.id.desc())
            .limit(10)
        ).all()

    # crude chunk count from Chroma files present (not exact, but useful)
    chroma_ok = os.path.isdir(CHROMA_DIR)
    return {
        "queries_total": qcount,
        "recent_queries": [{"question": q, "latency": l, "ts": str(ts)} for (q, l, ts) in last5],
        "recent_ingests": [{"filename": f, "chunks": c, "ts": str(ts)} for (f, c, ts) in ings],
        "chroma_path": CHROMA_DIR,
        "chroma_exists": chroma_ok,
        "uploads_dir": UPLOAD_DIR,
    }

@app.delete("/wipe_index/")
def wipe_index():
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return {"status": "ok", "message": "Index wiped. Reindex to rebuild."}
