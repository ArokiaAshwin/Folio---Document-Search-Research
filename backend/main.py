import os
import json
import time
import shutil
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings
from backend.auth import (
    register_user, authenticate_user, create_guest_user, create_access_token,
    get_current_user, UserRegister, UserLogin, UserResponse
)
from backend.document_processor import DocumentProcessor
from backend.rag_engine import rag_engine
from backend.llm_engine import llm_engine

app = FastAPI(
    title="AI Document Q&A Chatbot API",
    description="Fullstack RAG pipeline with FastAPI, ChromaDB, and GenAI LLMs",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOCS_META_FILE = os.path.join(settings.BASE_DIR, "documents_meta.json")
CHAT_HISTORY_FILE = os.path.join(settings.BASE_DIR, "chat_history.json")

def _load_meta() -> dict:
    if os.path.exists(DOCS_META_FILE):
        try:
            with open(DOCS_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_meta(data: dict):
    with open(DOCS_META_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _load_chat_history() -> dict:
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_chat_history(data: dict):
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ----------------- Auth Endpoints -----------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(req: UserRegister):
    user = register_user(req)
    token = create_access_token({"sub": user.id, "username": user.username, "is_guest": False})
    return TokenResponse(access_token=token, user=user)

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(req: UserLogin):
    user = authenticate_user(req)
    token = create_access_token({"sub": user.id, "username": user.username, "is_guest": False})
    return TokenResponse(access_token=token, user=user)

@app.post("/api/auth/guest", response_model=TokenResponse)
async def guest_login():
    guest = create_guest_user()
    token = create_access_token({"sub": guest.id, "username": guest.username, "is_guest": True})
    return TokenResponse(access_token=token, user=guest)

@app.get("/api/auth/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# ----------------- Document Endpoints -----------------

@app.post("/api/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
    current_user: UserResponse = Depends(get_current_user)
):
    c_size = chunk_size or settings.get("CHUNK_SIZE", 1000)
    c_overlap = chunk_overlap or settings.get("CHUNK_OVERLAP", 200)

    uploaded_results = []
    meta_db = _load_meta()

    for file in files:
        doc_id = str(uuid.uuid4())[:12]
        safe_filename = Path(file.filename).name
        save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{safe_filename}")

        # Save uploaded file
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(save_path)

        try:
            # Process & chunk
            chunks = DocumentProcessor.process_document(
                file_path=save_path,
                filename=safe_filename,
                document_id=doc_id,
                chunk_size=c_size,
                chunk_overlap=c_overlap
            )

            # Store in ChromaDB
            indexed_count = rag_engine.add_document_chunks(chunks)

            doc_entry = {
                "id": doc_id,
                "filename": safe_filename,
                "user_id": current_user.id,
                "size_bytes": file_size,
                "total_chunks": indexed_count,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "file_path": save_path
            }
            meta_db[doc_id] = doc_entry

            uploaded_results.append({
                "id": doc_id,
                "filename": safe_filename,
                "chunks_indexed": indexed_count,
                "status": "success"
            })
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            uploaded_results.append({
                "filename": safe_filename,
                "status": "error",
                "error": str(e)
            })

    _save_meta(meta_db)
    return {"results": uploaded_results, "total_uploaded": len(uploaded_results)}

@app.get("/api/documents")
async def list_documents(current_user: UserResponse = Depends(get_current_user)):
    meta_db = _load_meta()
    # Filter documents by user if not admin/guest
    user_docs = [
        doc for doc in meta_db.values()
        if doc.get("user_id") == current_user.id or current_user.is_guest
    ]
    user_docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"documents": user_docs, "total": len(user_docs), "stats": rag_engine.get_stats()}

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: UserResponse = Depends(get_current_user)):
    meta_db = _load_meta()
    if doc_id not in meta_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = meta_db[doc_id]
    # Delete from ChromaDB
    rag_engine.delete_document_chunks(doc_id)

    # Delete physical file
    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    del meta_db[doc_id]
    _save_meta(meta_db)
    return {"status": "success", "message": f"Document {doc.get('filename')} deleted"}

@app.get("/api/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: str, current_user: UserResponse = Depends(get_current_user)):
    chunks = rag_engine.get_document_chunks(doc_id)
    return {"chunks": chunks, "count": len(chunks)}

# ----------------- Chat & RAG Endpoints -----------------

class QueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    top_k: Optional[int] = None

@app.post("/api/chat/query")
async def query_documents(req: QueryRequest, current_user: UserResponse = Depends(get_current_user)):
    start_time = time.time()
    
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    top_k = req.top_k or settings.get("TOP_K_RESULTS", 4)
    
    # 1. Retrieve relevant chunks from ChromaDB
    retrieved_chunks = rag_engine.query_similar_chunks(
        query=req.query,
        n_results=top_k,
        document_id=req.document_id
    )

    # 2. Generate grounded answer
    result = llm_engine.generate_answer(
        query=req.query,
        retrieved_chunks=retrieved_chunks,
        provider=req.provider,
        model_name=req.model,
        api_key=req.api_key
    )

    elapsed_ms = round((time.time() - start_time) * 1000)

    # 3. Store in conversation history
    history = _load_chat_history()
    user_history = history.setdefault(current_user.id, [])
    
    chat_entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": req.query,
        "answer": result["answer"],
        "provider": result.get("provider"),
        "model": result.get("model"),
        "citations": result.get("citations", []),
        "latency_ms": elapsed_ms,
        "document_filter": req.document_id
    }
    user_history.append(chat_entry)
    _save_chat_history(history)

    return {
        "answer": result["answer"],
        "citations": result.get("citations", []),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "latency_ms": elapsed_ms,
        "total_chunks_searched": len(retrieved_chunks)
    }

@app.get("/api/chat/history")
async def get_chat_history(current_user: UserResponse = Depends(get_current_user)):
    history = _load_chat_history()
    return {"history": history.get(current_user.id, [])}

@app.delete("/api/chat/history")
async def clear_chat_history(current_user: UserResponse = Depends(get_current_user)):
    history = _load_chat_history()
    history[current_user.id] = []
    _save_chat_history(history)
    return {"status": "success", "message": "Chat history cleared"}

# ----------------- Settings / Diagnostics -----------------

class SettingsUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k: Optional[int] = None

@app.get("/api/settings")
async def get_settings():
    has_gemini = bool(settings.get("GEMINI_API_KEY"))
    has_openai = bool(settings.get("OPENAI_API_KEY"))
    return {
        "provider": settings.get("DEFAULT_LLM_PROVIDER", "gemini"),
        "model": settings.get("DEFAULT_MODEL", "gemini-2.0-flash"),
        "chunk_size": settings.get("CHUNK_SIZE", 1000),
        "chunk_overlap": settings.get("CHUNK_OVERLAP", 200),
        "top_k": settings.get("TOP_K_RESULTS", 4),
        "has_gemini_key": has_gemini,
        "has_openai_key": has_openai,
        "vector_stats": rag_engine.get_stats()
    }

@app.post("/api/settings")
async def update_settings(update: SettingsUpdate):
    if update.provider is not None:
        settings.set("DEFAULT_LLM_PROVIDER", update.provider)
    if update.model is not None:
        settings.set("DEFAULT_MODEL", update.model)
    if update.gemini_api_key is not None:
        settings.set("GEMINI_API_KEY", update.gemini_api_key)
    if update.openai_api_key is not None:
        settings.set("OPENAI_API_KEY", update.openai_api_key)
    if update.chunk_size is not None:
        settings.set("CHUNK_SIZE", update.chunk_size)
    if update.chunk_overlap is not None:
        settings.set("CHUNK_OVERLAP", update.chunk_overlap)
    if update.top_k is not None:
        settings.set("TOP_K_RESULTS", update.top_k)
    return {"status": "success", "message": "Settings updated"}

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "AI Document Q&A Chatbot",
        "chroma_chunks": rag_engine.collection.count()
    }

# Serve static frontend build if it exists
frontend_dist = os.path.join(settings.BASE_DIR.parent, "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend build index not found")

