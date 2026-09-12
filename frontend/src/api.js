const API_BASE = '/api';

export const getStoredToken = () => localStorage.getItem('documind_token');
export const setStoredToken = (token) => localStorage.setItem('documind_token', token);
export const removeStoredToken = () => localStorage.removeItem('documind_token');

const getAuthHeaders = () => {
  const token = getStoredToken();
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const api = {
  // Auth
  async login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setStoredToken(data.access_token);
    return data;
  },

  async register(username, email, password) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    setStoredToken(data.access_token);
    return data;
  },

  async guestLogin() {
    const res = await fetch(`${API_BASE}/auth/guest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) {
      throw new Error('Guest login failed');
    }
    const data = await res.json();
    setStoredToken(data.access_token);
    return data;
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return null;
    return await res.json();
  },

  // Documents
  async listDocuments() {
    const res = await fetch(`${API_BASE}/documents`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch documents');
    return await res.json();
  },

  async uploadDocuments(files, chunkSize, chunkOverlap) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    if (chunkSize) formData.append('chunk_size', chunkSize);
    if (chunkOverlap) formData.append('chunk_overlap', chunkOverlap);

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return await res.json();
  },

  async deleteDocument(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to delete document');
    return await res.json();
  },

  async getDocumentChunks(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}/chunks`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch document chunks');
    return await res.json();
  },

  // Chat & RAG
  async queryChat({ query, documentId, provider, model, topK }) {
    const res = await fetch(`${API_BASE}/chat/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        query,
        document_id: documentId,
        provider,
        model,
        top_k: topK
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Query failed');
    }
    return await res.json();
  },

  async getChatHistory() {
    const res = await fetch(`${API_BASE}/chat/history`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return { history: [] };
    return await res.json();
  },

  async clearChatHistory() {
    const res = await fetch(`${API_BASE}/chat/history`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to clear history');
    return await res.json();
  },

  // Settings
  async getSettings() {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to load settings');
    return await res.json();
  },

  async updateSettings(settings) {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return await res.json();
  }
};
