# AI Document Q&A Chatbot | Fullstack RAG System

A production-grade, GenAI-powered document question-answering chatbot that allows users to upload documents (PDF, DOCX, TXT, Markdown) and ask natural language questions with verifiable, grounded citations and source provenance.

---

## Key Highlights & Features

- **RAG (Retrieval-Augmented Generation) Pipeline**:
  - Recursive boundary document chunking respecting paragraph, sentence, and word hierarchies with configurable overlap.
  - High-performance vector similarity search powered by **ChromaDB** using persistent local vector embeddings (`all-MiniLM-L6-v2`).
- **Multi-Format Document Ingestion**:
  - Native support for **PDF** (`pypdf`), **Word Documents** (`docx`), **Markdown**, and **Plain Text**.
  - Tracks metadata per chunk: document ID, filename, exact page number, and chunk index.
- **Dual LLM & Extractive Fallback Engine**:
  - Integrated with **Google Gemini** (`google.genai` SDK for Gemini 2.0 Flash / 1.5 Pro).
  - Integrated with **OpenAI** (`gpt-4o`, `gpt-4o-mini`).
  - Built-in **Local Extractive RAG Mode**: works out-of-the-box even without an API key by extracting and synthesizing the highest-scoring vector matches.
- **Grounded Answers & Clickable Citations**:
  - Interactive source citation chips: `[Doc: filename, Page: X]` with vector similarity match scores.
  - Clicking any citation opens the **Source Evidence Inspector Drawer** revealing the exact chunk text.
- **Chunk Inspector**:
  - Inspect all parsed chunks, token/char lengths, and vector persistence status directly from the UI.
- **Security & Authentication**:
  - JWT (HMAC-SHA256) bearer token authentication.
  - PBKDF2-HMAC-SHA256 password hashing with salt and 100,000 iterations.
  - Instant **Demo Guest Mode** for friction-free exploration.
- **Modern Glassmorphic React Frontend**:
  - Futuristic dark-mode interface built with React, Vite, and Vanilla CSS.
  - Responsive document sidebar, drag & drop uploader, chat history export, and interactive model tuning.

---

## Architecture Diagram

```
+-------------------------------------------------------------+
|               React + Vite Frontend (Port 5173)              |
|  - Glassmorphic UI  - Citations Drawer  - Chunk Inspector   |
+------------------------------+------------------------------+
                               | REST API (JWT Bearer)
+------------------------------v------------------------------+
|                    Flask Backend (Port 8000)                |
|  +--------------------------------------------------------+  |
|  | Auth Service (JWT + PBKDF2 Password Hashing)           |  |
|  +--------------------------------------------------------+  |
|  | Document Processor (PDF / DOCX / TXT Splitter)         |  |
|  +--------------------------------------------------------+  |
|  | RAG Engine (ChromaDB PersistentClient Vector Index)    |  |
|  +--------------------------------------------------------+  |
|  | LLM Engine (Gemini 2.0 / OpenAI / Extractive Fallback) |  |
|  +--------------------------------------------------------+  |
+------------------------------+------------------------------+
                               |
                +--------------v-------------+
                | ChromaDB Local Vector Store |
                |      (./backend/chroma_db) |
                +----------------------------+
```

---

## Directory Structure

```
QA chatbot/
├── backend/
│   ├── chroma_db/            # ChromaDB persistent vector database
│   ├── tests/                # Unit & E2E integration test suite
│   │   ├── test_rag.py       # Auth, Chunker, and ChromaDB tests
│   │   ├── test_api.py       # Flask endpoints unit tests
│   │   └── test_e2e.py       # Full end-to-end RAG upload & Q&A test
│   ├── uploads/              # Storage directory for uploaded documents
│   ├── auth.py               # JWT generation, validation & password hashing
│   ├── config.py             # Settings and environment variable loader
│   ├── document_processor.py # Multi-format parser & recursive chunker
│   ├── llm_engine.py         # Gemini, OpenAI, and local extractive fallback
│   ├── main.py               # Flask application with REST endpoints & static mount
│   ├── rag_engine.py         # ChromaDB client & vector similarity search
│   ├── requirements.txt      # Python dependencies (Flask, ChromaDB, etc.)
│   └── .env                  # Environment variables & API key configurations
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthModal.jsx           # Sign in, Sign up & Guest mode modal
│   │   │   ├── ChatInterface.jsx       # Chat stream, suggestions, input box
│   │   │   ├── ChatMessage.jsx         # Markdown render & interactive citation chips
│   │   │   ├── ChunkInspectorModal.jsx # Visual inspection of vector chunks
│   │   │   ├── CitationDrawer.jsx      # Source evidence drawer
│   │   │   ├── DocumentSidebar.jsx     # Drag & drop uploader & doc list
│   │   │   ├── Navbar.jsx              # Header, stats pill & settings trigger
│   │   │   └── SettingsModal.jsx       # API keys, models & Top-K tuning
│   │   ├── api.js            # API client with token management
│   │   ├── App.jsx           # Root React component
│   │   ├── index.css         # Modern glassmorphic vanilla CSS design system
│   │   └── main.jsx          # React DOM entry point
│   ├── index.html            # Web app entry with Google Fonts
│   ├── package.json          # Frontend packages & scripts
│   └── vite.config.js        # Vite config with API proxy
└── sample_docs/              # Ready-to-use sample documents (PDF, DOCX, TXT)
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
Navigate to the root directory and install backend requirements:
```bash
pip install -r backend/requirements.txt
```

*(Optional)* Configure your Google Gemini or OpenAI API Key in `backend/.env` or configure it directly through the UI Settings dialog:
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

Start the Flask server:
```bash
python backend/main.py
```
*(Alternatively: `python -m backend.main` or `flask --app backend.main run --port 8000`)*

### 3. Frontend Setup
In a separate terminal, navigate to the `frontend` folder:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

*(Note: The Flask backend also serves the built React application directly at `http://127.0.0.1:8000` when the production bundle is built via `npm run build`).*

---

## Running Automated Tests

Run the full suite of unit and integration tests:
```bash
# Auth, Chunker, and ChromaDB Tests
python -m unittest backend/tests/test_rag.py

# Flask Endpoints Unit Tests
python -m unittest backend/tests/test_api.py

# Complete End-to-End RAG Verification (with Flask server running)
python backend/tests/test_e2e.py
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new user account |
| `POST` | `/api/auth/login` | Sign in with username & password |
| `POST` | `/api/auth/guest` | Instant demo guest session |
| `POST` | `/api/documents/upload` | Multipart upload for PDF, DOCX, TXT, MD |
| `GET` | `/api/documents` | List uploaded documents & ChromaDB stats |
| `DELETE` | `/api/documents/{id}` | Delete document and remove ChromaDB vectors |
| `GET` | `/api/documents/{id}/chunks` | Inspect all chunks for a document |
| `POST` | `/api/chat/query` | RAG semantic retrieval & answer generation |
| `GET` | `/api/chat/history` | Retrieve user chat history |
| `DELETE` | `/api/chat/history` | Clear conversation history |
| `GET` | `/api/settings` | Get current model and vector stats |
| `POST` | `/api/settings` | Update runtime LLM provider, keys, and Top-K |
| `GET` | `/api/health` | Health check & vector count |
