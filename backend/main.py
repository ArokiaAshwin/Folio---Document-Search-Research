import os
import sys
import json
import time
import shutil
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in sys.path when running as a direct script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS

from backend.config import settings
from backend.auth import (
    register_user, authenticate_user, create_guest_user, create_access_token,
    get_current_user, google_authenticate, UserRegister, UserLogin, UserResponse, AuthError
)
from backend.document_processor import DocumentProcessor
from backend.rag_engine import rag_engine
from backend.llm_engine import llm_engine

app = Flask(__name__)

# CORS configuration
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Error handlers
@app.errorhandler(AuthError)
def handle_auth_error(e: AuthError):
    return jsonify({"detail": e.detail}), e.status_code

@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({"detail": getattr(e, "description", "Bad Request")}), 400

@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({"detail": getattr(e, "description", "Not Found")}), 404

@app.errorhandler(500)
def handle_server_error(e):
    return jsonify({"detail": getattr(e, "description", "Internal Server Error")}), 500

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

@app.post("/api/auth/register")
def register():
    data = request.get_json() or {}
    try:
        req = UserRegister(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

    user = register_user(req)
    token = create_access_token({"sub": user.id, "username": user.username, "is_guest": False})
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict()
    }), 200

@app.post("/api/auth/login")
def login():
    data = request.get_json() or {}
    try:
        req = UserLogin(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

    user = authenticate_user(req)
    token = create_access_token({"sub": user.id, "username": user.username, "is_guest": False})
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict()
    }), 200

@app.post("/api/auth/guest")
def guest_login():
    guest = create_guest_user()
    token = create_access_token({"sub": guest.id, "username": guest.username, "is_guest": True})
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user": guest.to_dict()
    }), 200

@app.get("/api/auth/config")
def auth_config():
    return jsonify({
        "google_client_id": settings.get("GOOGLE_CLIENT_ID", "")
    }), 200

@app.post("/api/auth/google")
def google_login():
    data = request.get_json() or {}
    credential = data.get("credential")
    if not credential:
        return jsonify({"detail": "Missing Google credential token"}), 400

    user = google_authenticate(credential)
    token = create_access_token({"sub": user.id, "username": user.username, "is_guest": False})
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict()
    }), 200

@app.get("/api/auth/me")
def me():
    current_user = get_current_user()
    return jsonify(current_user.to_dict()), 200

# ----------------- Document Endpoints -----------------

@app.post("/api/documents/upload")
def upload_documents():
    current_user = get_current_user()
    files = request.files.getlist("files")
    if not files:
        return jsonify({"detail": "No files uploaded"}), 400

    chunk_size = request.form.get("chunk_size", type=int)
    chunk_overlap = request.form.get("chunk_overlap", type=int)

    c_size = chunk_size or settings.get("CHUNK_SIZE", 1000)
    c_overlap = chunk_overlap or settings.get("CHUNK_OVERLAP", 200)

    uploaded_results = []
    meta_db = _load_meta()

    for file in files:
        if not file.filename:
            continue
        doc_id = str(uuid.uuid4())[:12]
        safe_filename = Path(file.filename).name
        save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{safe_filename}")

        # Save uploaded file
        file.save(save_path)
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
    return jsonify({"results": uploaded_results, "total_uploaded": len(uploaded_results)}), 200

@app.get("/api/documents")
def list_documents():
    current_user = get_current_user()
    meta_db = _load_meta()
    user_docs = [
        doc for doc in meta_db.values()
        if doc.get("user_id") == current_user.id or current_user.is_guest
    ]
    user_docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jsonify({"documents": user_docs, "total": len(user_docs), "stats": rag_engine.get_stats()}), 200

@app.delete("/api/documents/<doc_id>")
def delete_document(doc_id: str):
    get_current_user()
    meta_db = _load_meta()
    if doc_id not in meta_db:
        return jsonify({"detail": "Document not found"}), 404

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
    return jsonify({"status": "success", "message": f"Document {doc.get('filename')} deleted"}), 200

@app.get("/api/documents/<doc_id>/chunks")
def get_document_chunks(doc_id: str):
    get_current_user()
    chunks = rag_engine.get_document_chunks(doc_id)
    return jsonify({"chunks": chunks, "count": len(chunks)}), 200

# ----------------- Chat & RAG Endpoints -----------------

@app.post("/api/chat/query")
def query_documents():
    current_user = get_current_user()
    start_time = time.time()
    data = request.get_json() or {}
    
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"detail": "Query cannot be empty"}), 400

    document_id = data.get("document_id")
    provider = data.get("provider")
    model = data.get("model")
    api_key = data.get("api_key")
    top_k = data.get("top_k") or settings.get("TOP_K_RESULTS", 4)

    # 1. Retrieve relevant chunks from ChromaDB
    retrieved_chunks = rag_engine.query_similar_chunks(
        query=query,
        n_results=top_k,
        document_id=document_id
    )

    # 2. Generate grounded answer
    result = llm_engine.generate_answer(
        query=query,
        retrieved_chunks=retrieved_chunks,
        provider=provider,
        model_name=model,
        api_key=api_key
    )

    elapsed_ms = round((time.time() - start_time) * 1000)

    # 3. Store in conversation history
    history = _load_chat_history()
    user_history = history.setdefault(current_user.id, [])

    chat_entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "answer": result["answer"],
        "provider": result.get("provider"),
        "model": result.get("model"),
        "citations": result.get("citations", []),
        "latency_ms": elapsed_ms,
        "document_filter": document_id
    }
    user_history.append(chat_entry)
    _save_chat_history(history)

    return jsonify({
        "answer": result["answer"],
        "citations": result.get("citations", []),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "latency_ms": elapsed_ms,
        "total_chunks_searched": len(retrieved_chunks)
    }), 200

@app.get("/api/chat/history")
def get_chat_history():
    current_user = get_current_user()
    history = _load_chat_history()
    return jsonify({"history": history.get(current_user.id, [])}), 200

@app.delete("/api/chat/history")
def clear_chat_history():
    current_user = get_current_user()
    history = _load_chat_history()
    history[current_user.id] = []
    _save_chat_history(history)
    return jsonify({"status": "success", "message": "Chat history cleared"}), 200

# ----------------- Settings / Diagnostics -----------------

@app.get("/api/settings")
def get_settings():
    has_gemini = bool(settings.get("GEMINI_API_KEY"))
    has_openai = bool(settings.get("OPENAI_API_KEY"))
    return jsonify({
        "provider": settings.get("DEFAULT_LLM_PROVIDER", "gemini"),
        "model": settings.get("DEFAULT_MODEL", "gemini-2.0-flash"),
        "chunk_size": settings.get("CHUNK_SIZE", 1000),
        "chunk_overlap": settings.get("CHUNK_OVERLAP", 200),
        "top_k": settings.get("TOP_K_RESULTS", 4),
        "has_gemini_key": has_gemini,
        "has_openai_key": has_openai,
        "vector_stats": rag_engine.get_stats()
    }), 200

@app.post("/api/settings")
def update_settings():
    update = request.get_json() or {}
    if update.get("provider") is not None:
        settings.set("DEFAULT_LLM_PROVIDER", update["provider"])
    if update.get("model") is not None:
        settings.set("DEFAULT_MODEL", update["model"])
    if update.get("gemini_api_key") is not None:
        settings.set("GEMINI_API_KEY", update["gemini_api_key"])
    if update.get("openai_api_key") is not None:
        settings.set("OPENAI_API_KEY", update["openai_api_key"])
    if update.get("chunk_size") is not None:
        settings.set("CHUNK_SIZE", update["chunk_size"])
    if update.get("chunk_overlap") is not None:
        settings.set("CHUNK_OVERLAP", update["chunk_overlap"])
    if update.get("top_k") is not None:
        settings.set("TOP_K_RESULTS", update["top_k"])
    return jsonify({"status": "success", "message": "Settings updated"}), 200

@app.get("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "AI Document Q&A Chatbot",
        "chroma_chunks": rag_engine.collection.count()
    }), 200

# ----------------- Serve static frontend build if it exists -----------------
frontend_dist = os.path.join(settings.BASE_DIR.parent, "frontend", "dist")

@app.route("/assets/<path:path>")
def serve_assets(path):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        return send_from_directory(assets_dir, path)
    abort(404)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    if path.startswith("api"):
        return jsonify({"detail": "API route not found"}), 404
    if os.path.exists(os.path.join(frontend_dist, path)) and os.path.isfile(os.path.join(frontend_dist, path)):
        return send_from_directory(frontend_dist, path)
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return send_from_directory(frontend_dist, "index.html")
    return jsonify({
        "status": "running",
        "message": "AI Document Q&A Chatbot Flask Backend is running. Run the React frontend using npm run dev or build dist."
    }), 200

if __name__ == "__main__":
    print(f"Starting Flask server on {settings.HOST}:{settings.PORT}...")
    app.run(host=settings.HOST, port=settings.PORT, debug=True)
