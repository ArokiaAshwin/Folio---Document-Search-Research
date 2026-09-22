# Folio — AI Document Search & Q&A Assistant | Fullstack RAG System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)

A production-ready, fullstack Retrieval-Augmented Generation (RAG) platform. Upload internal documents (PDF, DOCX, TXT, Markdown) and ask natural language questions with verifiable, grounded citations and source provenance.

Includes full **User Authentication** (Email/Password, Confirm Password validation, Google OAuth 2.0, Guest preview) and 1-click **Live Production Deployment** configurations for Render, Railway, and Docker.

---

## Key Features

- **Mandatory Authentication & Page Gating**:
  - Gated landing experience: visitors are welcomed with a sleek **Sign In** screen.
  - **Email & Password Login**: Fast, secure login with show/hide password toggle.
  - **Sign Up with Confirm Password**: Real-time password match validation before account creation.
  - **Google Sign-In (OAuth 2.0)**: Integrated via Google Identity Services (GIS) with instant interactive demo fallback.
  - **Guest Access**: 1-click preview mode for immediate testing.
- **Advanced RAG Pipeline**:
  - Recursive boundary chunking with configurable overlap respecting paragraph, sentence, and word hierarchies.
  - High-performance vector similarity search powered by **ChromaDB** with persistent disk storage (`all-MiniLM-L6-v2`).
- **Multi-Format Document Parsing**:
  - Native parsing for **PDF** (`pypdf`), **Word Documents** (`docx`), **Markdown**, and **Plain Text**.
  - Precise page-number and chunk metadata tracking.
- **Dual LLM & Extractive Fallback Engine**:
  - **Google Gemini**: Gemini 2.0 Flash / 1.5 Pro via `google.genai` SDK.
  - **OpenAI**: GPT-4o / GPT-4o-mini support.
  - **Local Extractive RAG Mode**: Works out-of-the-box even without an external API key.
- **Grounded Answers & Interactive Citations**:
  - Clickable citation chips: `[Doc: filename, Page: X]` with vector similarity match scores.
  - **Source Evidence Drawer**: Inspect the exact chunk text extracted from the source document.
- **Chunk Inspector**:
  - Inspect all parsed chunks, token/character lengths, and vector persistence status directly from the UI.
- **Production-Ready & Cloud Deployable**:
  - Multi-stage `Dockerfile` (builds React Vite frontend and serves via Flask + Gunicorn).
  - Pre-configured blueprints for **Render.com**, **Railway.app**, and **Docker Compose**.

---

## System Architecture

```
+-------------------------------------------------------------------------+
|                  React + Vite Frontend (Port 5173 / SPA)                 |
|  - AuthPage (Email / Password / Confirm / Google)  - Citation Drawer    |
|  - Document Sidebar & Uploader                     - Chunk Inspector    |
+------------------------------------+------------------------------------+
                                     | REST API (JWT Bearer)
+------------------------------------v------------------------------------+
|                         Flask Backend (Port 8000)                       |
|  +-------------------------------------------------------------------+  |
|  | Auth Module (JWT, PBKDF2 Password Hashing, Google OAuth2 verify)  |  |
|  +-------------------------------------------------------------------+  |
|  | Document Processor (PDF / DOCX / TXT / MD Recursive Splitter)     |  |
|  +-------------------------------------------------------------------+  |
|  | RAG Engine (ChromaDB PersistentClient Vector Search)              |  |
|  +-------------------------------------------------------------------+  |
|  | LLM Engine (Gemini 2.0 Flash / OpenAI GPT-4o / Extractive Mode)   |  |
|  +-------------------------------------------------------------------+  |
+------------------------------------+------------------------------------+
                                     |
                      +--------------v--------------+
                      | ChromaDB Local Vector Store |
                      |    (./backend/chroma_db)    |
                      +-----------------------------+
```

---

## Directory Structure

```
QA chatbot/
├── Dockerfile                # Multi-stage production container
├── docker-compose.yml        # Docker Compose configuration with volume persistence
├── render.yaml               # 1-click cloud deployment blueprint for Render.com
├── railway.json              # Railway.app cloud deployment configuration
├── Procfile                  # Process definition for Heroku / Railway
├── DEPLOYMENT.md             # Complete step-by-step live deployment guide
├── README.md                 # Project documentation
├── requirements.txt          # Python root dependencies
├── sample_docs/              # Ready-to-use sample documents (PDF, DOCX, TXT)
│
├── backend/
│   ├── auth.py               # Authentication (JWT, PBKDF2, Google OAuth)
│   ├── config.py             # Settings & environment variable loader
│   ├── document_processor.py # PDF/DOCX/TXT parser & recursive chunker
│   ├── llm_engine.py         # Gemini, OpenAI & local extractive RAG
│   ├── main.py               # Flask application, REST routes & static SPA mount
│   ├── rag_engine.py         # ChromaDB client & vector similarity search
│   ├── requirements.txt      # Backend Python dependencies
│   ├── .env                  # Backend environment variables
│   └── tests/                # Automated test suite
│       ├── test_api.py       # API endpoints & auth unit tests
│       ├── test_rag.py       # Chunker & vector database tests
│       └── test_e2e.py       # Full end-to-end upload & query verification
│
└── frontend/
    ├── index.html            # Web app entry with Google Identity Services
    ├── package.json          # Node dependencies & build scripts
    ├── vite.config.js        # Vite config with API proxy
    └── src/
        ├── App.jsx           # Root component with auth gating
        ├── api.js            # API client with JWT & Google auth
        ├── index.css         # Modern dark-mode vanilla CSS design system
        └── components/
            ├── AuthPage.jsx            # Fullscreen Sign In / Sign Up / Google screen
            ├── AuthModal.jsx           # In-app authentication dialog
            ├── ChatInterface.jsx       # Chat stream & prompt suggestions
            ├── ChatMessage.jsx         # Markdown answer render with citation chips
            ├── ChunkInspectorModal.jsx # Visual inspection of vector chunks
            ├── CitationDrawer.jsx      # Source evidence drawer
            ├── DocumentSidebar.jsx     # Document upload & management sidebar
            ├── Navbar.jsx              # Header, stats badge & settings trigger
            └── SettingsModal.jsx       # LLM provider, models & Top-K tuning
```

---

## Quickstart Guide (Local Development)

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**

### 2. Backend Setup
1. Open a terminal in the root directory:
   ```bash
   pip install -r requirements.txt
   ```
2. *(Optional)* Configure your Google Gemini or OpenAI API key in `backend/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_CLIENT_ID=your_google_client_id_here
   ```
   *(Note: The app works out-of-the-box even without API keys using smart extractive RAG).*
3. Start the Flask server:
   ```bash
   python backend/main.py
   ```
   Server starts at `http://localhost:8000`.

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at **`http://localhost:5173`**.

---

## Running with Docker (1 Command)

Run both the frontend and backend with automatic ChromaDB volume persistence:
```bash
docker compose up -d --build
```
Access the application at **`http://localhost:8000`**.

---

## Deploying Live to the Cloud

For complete instructions, see the **[DEPLOYMENT.md](DEPLOYMENT.md)** guide.

### Free 1-Click Deployment on Render.com:
1. Push this repository to GitHub.
2. Sign in to [Render.com](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Connect your repository. Render will automatically detect the **`Dockerfile`**.
4. Add your environment variables:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `JWT_SECRET`: Random secure string
   - `GOOGLE_CLIENT_ID`: (Optional) Your Google Cloud OAuth Client ID
5. Click **Create Web Service**. Your app is live with a free public URL!

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new account (email, password, optional username) |
| `POST` | `/api/auth/login` | Sign in with email/username and password |
| `POST` | `/api/auth/google` | Authenticate via Google OAuth credential token |
| `GET` | `/api/auth/config` | Retrieve public client auth settings |
| `POST` | `/api/auth/guest` | Generate instant demo guest session |
| `GET` | `/api/auth/me` | Fetch authenticated user profile |
| `POST` | `/api/documents/upload` | Upload PDF, DOCX, TXT, or Markdown documents |
| `GET` | `/api/documents` | List uploaded documents & collection stats |
| `DELETE` | `/api/documents/{id}` | Delete document and delete vector embeddings |
| `GET` | `/api/documents/{id}/chunks`| Inspect all parsed vector chunks for a document |
| `POST` | `/api/chat/query` | RAG semantic retrieval & answer generation |
| `GET` | `/api/chat/history` | Retrieve user chat history |
| `DELETE` | `/api/chat/history` | Clear chat history |
| `GET` | `/api/settings` | Get runtime settings and LLM configuration |
| `POST` | `/api/settings` | Update LLM provider, API keys, and Top-K |
| `GET` | `/api/health` | Health check endpoint and total vector chunk count |

---

## Running Automated Tests

Run the full automated test suite:
```bash
# Run all unit and integration tests (Auth, Document Parser, ChromaDB, RAG)
python -m unittest discover backend/tests

# Run End-to-End RAG Pipeline verification (with Flask server running)
python backend/tests/test_e2e.py
```

---

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

