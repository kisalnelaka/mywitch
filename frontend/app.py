import os
import time
import requests
import pandas as pd
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="PDF Learning Assistant", layout="wide")
st.title("📚 PDF Learning Assistant (RAG + Ollama + Chroma)")

tabs = st.tabs(["📥 Upload / Ingest", "💬 Ask / Chat", "📊 Metrics"])

# ------------- Upload / Ingest -------------
with tabs[0]:
    st.header("Upload & Ingest PDFs")
    st.caption(f"Backend: {BACKEND_URL}")
    uploaded = st.file_uploader("Drop a PDF here", type=["pdf"])
    if uploaded and st.button("Upload & Index"):
        with st.spinner("Uploading and indexing..."):
            files = {"file": (uploaded.name, uploaded, "application/pdf")}
            r = requests.post(f"{BACKEND_URL}/upload_pdf/", files=files, timeout=300)
        if r.ok:
            st.success(r.json())
        else:
            st.error(r.text)

    st.markdown("—")
    if st.button("Reindex ALL from /data/uploads"):
        with st.spinner("Rebuilding entire index..."):
            r = requests.post(f"{BACKEND_URL}/reindex_all/")
        st.write(r.json())

    if st.button("Wipe Index"):
        with st.spinner("Deleting Chroma index..."):
            r = requests.delete(f"{BACKEND_URL}/wipe_index/")
        st.write(r.json())

# ------------- Ask / Chat -------------
with tabs[1]:
    st.header("Ask your PDFs")
    q = st.text_input("Enter a question")
    k = st.slider("Retriever k", 1, 10, 4)
    if st.button("Ask"):
        with st.spinner("Thinking (retrieval + generation)..."):
            r = requests.post(f"{BACKEND_URL}/ask/", data={"question": q, "k": k}, timeout=300)
        if r.ok:
            data = r.json()
            st.subheader("Answer")
            st.write(data["answer"])
            st.markdown(f"**Latency:** {data['latency']:.3f}s")

            st.subheader("Sources")
            for s in data["sources"]:
                st.markdown(f"- **{s['source']}** (page {s.get('page','?')})")
                st.code(s["preview"])
        else:
            st.error(r.text)

# ------------- Metrics -------------
with tabs[2]:
    st.header("Metrics")
    r = requests.get(f"{BACKEND_URL}/metrics/")
    if r.ok:
        m = r.json()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Queries", m["queries_total"])
            st.write("Recent Queries")
            if m["recent_queries"]:
                df = pd.DataFrame(m["recent_queries"])
                st.dataframe(df, use_container_width=True)
            else:
                st.write("No queries yet.")

        with col2:
            st.write("Recent Ingests")
            if m["recent_ingests"]:
                df2 = pd.DataFrame(m["recent_ingests"])
                st.dataframe(df2, use_container_width=True)
            else:
                st.write("No ingests yet.")

        st.markdown("—")
        st.write("Chroma:")
        st.json({"path": m["chroma_path"], "exists": m["chroma_exists"]})
        st.write("Uploads dir:")
        st.code(m["uploads_dir"])
    else:
        st.error(r.text)
