# Live Production Deployment Guide

This guide explains how to deploy **Folio (Document Search & RAG Chatbot)** live to the web.

---

## Architecture Overview for Live Deployment

In production, the application runs as a **single, unified service**:
1. **Frontend**: The React (Vite) app is built into static production assets (`frontend/dist`).
2. **Backend**: Flask serves both the REST API (`/api/*`) and the frontend single-page application (`/`), eliminating CORS issues and hosting costs.
3. **Database & Storage**: ChromaDB vector store and uploaded documents persist to disk.

---

## Option 1: Deploy Live on Render.com (Recommended — 100% Free)

[Render.com](https://render.com) offers free web service hosting and natively supports Docker containers.

### Step 1: Push Your Code to GitHub
If your project is not already on GitHub:
```bash
git init
git add .
git commit -m "Add authentication and live deployment setup"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

### Step 2: Create a Web Service on Render
1. Go to [https://dashboard.render.com/](https://dashboard.render.com/) and sign in.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Fill in the following settings:
   - **Name**: `folio-doc-search` (or your preferred name)
   - **Region**: Choose the closest region (e.g. Frankfurt, Oregon, Singapore)
   - **Environment**: **Docker** (Render will automatically detect the `Dockerfile`)
   - **Instance Type**: **Free**
5. Expand **Advanced** -> **Add Environment Variable**:
   | Key | Value | Description |
   |---|---|---|
   | `GEMINI_API_KEY` | `AIzaSy...` | Your Google Gemini API Key |
   | `OPENAI_API_KEY` | `sk-...` | (Optional) Your OpenAI API Key |
   | `GOOGLE_CLIENT_ID` | `...apps.googleusercontent.com` | (Optional) Google OAuth Client ID |
   | `JWT_SECRET` | `generate-a-random-secret-key-32-chars` | Secret key for auth tokens |
   | `DEFAULT_LLM_PROVIDER` | `gemini` | Default LLM provider (`gemini` or `openai`) |
   | `DEFAULT_MODEL` | `gemini-2.0-flash` | Default AI model |
6. Click **Create Web Service**.

Render will now build your React frontend, package the Python backend, and launch your live application at a public URL like:
`https://folio-doc-search.onrender.com`

---

## Option 2: Deploy on Railway.app

[Railway.app](https://railway.app) provides zero-config Docker deployment with persistent volume support:

1. Go to [https://railway.app](https://railway.app) and sign in.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository. Railway will detect `Dockerfile` automatically.
4. Go to **Variables** tab and add:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
   - `JWT_SECRET`: Random secure string
5. Go to **Settings** -> **Networking** -> **Generate Domain** to get your public live URL.

---

## Option 3: Deploy on Any Linux VPS (Ubuntu, Debian, AWS EC2, DigitalOcean)

If you have a cloud virtual private server:

1. **Install Docker & Docker Compose** on your server:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
   ```
2. **Clone your repository**:
   ```bash
   git clone https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
   cd <YOUR_REPO_NAME>
   ```
3. **Configure environment variables**:
   Create a `.env` file in the root directory:
   ```env
   PORT=8000
   GEMINI_API_KEY=your_gemini_key_here
   GOOGLE_CLIENT_ID=your_google_client_id_here
   JWT_SECRET=supersecret-live-production-jwt-key
   ```
4. **Launch with Docker Compose**:
   ```bash
   docker compose up -d --build
   ```
5. Your application is live at `http://<YOUR_SERVER_IP>:8000`!
   *(You can set up Nginx and a free Let's Encrypt SSL certificate with Certbot for HTTPS).*

---

## Configuring Google Sign-In (OAuth 2.0)

To enable live Google Sign-In:

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Go to **APIs & Services** -> **Credentials**.
4. Click **Create Credentials** -> **OAuth Client ID**.
5. Select **Web application**.
6. Under **Authorized JavaScript origins**, add:
   - `http://localhost:5173` (for local development)
   - `http://localhost:8000` (for local Docker/backend)
   - `https://your-app.onrender.com` (your live production URL)
7. Click **Create** and copy your **Client ID** (it looks like `1234567890-abcdef.apps.googleusercontent.com`).
8. Add this Client ID to your live environment variables:
   `GOOGLE_CLIENT_ID=<YOUR_CLIENT_ID>`

> **Note**: Even before you configure a Google Cloud Client ID, the app includes an interactive Google Sign-In preview so you and your users can test Google authentication out of the box!

---

## Verification & Health Check

Once deployed live:
- Check backend health: `https://your-domain/api/health`
- Check auth config: `https://your-domain/api/auth/config`
- Open `https://your-domain/`:
  - You will be greeted with the Login page.
  - Test registration with email, password, and confirm password.
  - Test logging in and uploading documents.
