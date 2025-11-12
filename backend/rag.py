import os
from typing import List, Dict, Any
from datetime import datetime
from PyPDF2 import PdfReader

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA

CHROMA_DIR = os.getenv("CHROMA_DIR", "/data/chroma")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/data/uploads")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# singletons
_embeddings = None
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        # Good, fast local embedder
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings

def get_splitter():
    return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

def get_vectordb():
    # Ensure dir exists
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=get_embeddings())

def make_llm():
    # LangChain Chat wrapper for Ollama server
    return ChatOllama(base_url=OLLAMA_HOST, model=OLLAMA_MODEL, temperature=0)

def pdf_to_pages_text(path: str) -> List[Dict[str, Any]]:
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt.strip():
            pages.append({"page": i, "text": txt})
    return pages

def ingest_pdf(path: str) -> int:
    """Parse, split, embed, and upsert into Chroma. Returns chunk count."""
    filename = os.path.basename(path)
    pages = pdf_to_pages_text(path)
    splitter = get_splitter()

    docs = []
    metadatas = []
    for p in pages:
        chunks = splitter.split_text(p["text"])
        for ch in chunks:
            docs.append(ch)
            metadatas.append({
                "source": filename,
                "page": p["page"],
                "ingested_at": datetime.utcnow().isoformat()
            })
    if not docs:
        return 0

    vectordb = get_vectordb()
    vectordb.add_texts(docs, metadatas)
    vectordb.persist()
    return len(docs)

def rebuild_from_uploads() -> int:
    # Drop and rebuild
    if os.path.exists(CHROMA_DIR):
        for root, dirs, files in os.walk(CHROMA_DIR, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
    os.makedirs(CHROMA_DIR, exist_ok=True)

    total = 0
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        return 0
    for fname in os.listdir(UPLOAD_DIR):
        if fname.lower().endswith(".pdf"):
            total += ingest_pdf(os.path.join(UPLOAD_DIR, fname))
    return total

def qa_answer(question: str, k: int = 4) -> Dict[str, Any]:
    vectordb = get_vectordb()
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    llm = make_llm()

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
    )
    result = chain({"query": question})
    answer = result.get("result", "")
    src_docs = result.get("source_documents", [])

    sources = [{
        "source": d.metadata.get("source"),
        "page": d.metadata.get("page"),
        "preview": (d.page_content[:500] + "…") if len(d.page_content) > 500 else d.page_content
    } for d in src_docs]

    return {"answer": answer, "sources": sources}
