import React, { useState, useEffect } from 'react';
import { api, getStoredToken, removeStoredToken } from './api';
import Navbar from './components/Navbar';
import DocumentSidebar from './components/DocumentSidebar';
import ChatInterface from './components/ChatInterface';
import CitationDrawer from './components/CitationDrawer';
import SettingsModal from './components/SettingsModal';
import AuthModal from './components/AuthModal';
import AuthPage from './components/AuthPage';
import ChunkInspectorModal from './components/ChunkInspectorModal';

export default function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState({ total_chunks: 0 });
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingChat, setLoadingChat] = useState(false);
  
  // Modals & Drawers
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [activeCitation, setActiveCitation] = useState(null);
  const [inspectorDoc, setInspectorDoc] = useState(null);
  const [inspectorChunks, setInspectorChunks] = useState([]);
  const [loadingInspector, setLoadingInspector] = useState(false);

  // App settings state
  const [settingsData, setSettingsData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Initialize App
  useEffect(() => {
    initApp();
  }, []);

  const initApp = async () => {
    try {
      const token = getStoredToken();
      if (token) {
        const currentUser = await api.getMe().catch(() => null);
        if (currentUser) {
          setUser(currentUser);
          await loadWorkspaceData();
        } else {
          removeStoredToken();
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } catch (err) {
      console.error('Initialization error:', err);
      setUser(null);
    } finally {
      setAuthChecked(true);
    }
  };

  const loadWorkspaceData = async () => {
    try {
      // 1. Fetch Settings
      const s = await api.getSettings().catch(() => null);
      setSettingsData(s);

      // 2. Fetch Documents
      await refreshDocuments();

      // 3. Fetch Chat History
      const h = await api.getChatHistory().catch(() => ({ history: [] }));
      if (h.history && h.history.length > 0) {
        const formatted = [];
        h.history.forEach(item => {
          formatted.push({ sender: 'user', text: item.query });
          formatted.push({
            sender: 'ai',
            text: item.answer,
            citations: item.citations,
            model: item.model,
            latency_ms: item.latency_ms
          });
        });
        setMessages(formatted);
      }
    } catch (err) {
      console.error('Failed to load workspace data:', err);
    }
  };

  const handleAuthSuccess = async (authenticatedUser) => {
    setUser(authenticatedUser);
    await loadWorkspaceData();
  };

  const refreshDocuments = async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data.documents || []);
      setStats(data.stats || { total_chunks: 0 });
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleUpload = async (files) => {
    setUploading(true);
    setUploadError(null);
    try {
      await api.uploadDocuments(files);
      await refreshDocuments();
      const s = await api.getSettings();
      setSettingsData(s);
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to remove "${filename}" from the knowledge base?`)) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      if (selectedDocId === docId) setSelectedDocId(null);
      await refreshDocuments();
      const s = await api.getSettings();
      setSettingsData(s);
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  const handleInspectChunks = async (doc) => {
    setInspectorDoc(doc);
    setLoadingInspector(true);
    try {
      const res = await api.getDocumentChunks(doc.id);
      setInspectorChunks(res.chunks || []);
    } catch (err) {
      console.error(err);
      setInspectorChunks([]);
    } finally {
      setLoadingInspector(false);
    }
  };

  const handleSendMessage = async (queryText) => {
    if (!queryText.trim()) return;

    // Add user message to stream
    const newMessages = [...messages, { sender: 'user', text: queryText }];
    setMessages(newMessages);
    setLoadingChat(true);

    try {
      const response = await api.queryChat({
        query: queryText,
        documentId: selectedDocId,
        provider: settingsData?.provider,
        model: settingsData?.model,
        topK: settingsData?.top_k
      });

      setMessages([
        ...newMessages,
        {
          sender: 'ai',
          text: response.answer,
          citations: response.citations || [],
          model: response.model,
          latency_ms: response.latency_ms
        }
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          sender: 'ai',
          text: `⚠️ **Query Error**: ${err.message || 'An error occurred during retrieval or generation.'}`
        }
      ]);
    } finally {
      setLoadingChat(false);
    }
  };

  const handleClearChat = async () => {
    if (messages.length === 0) return;
    if (window.confirm('Clear entire conversation history?')) {
      await api.clearChatHistory();
      setMessages([]);
    }
  };

  const handleSaveSettings = async (newSettings) => {
    await api.updateSettings(newSettings);
    const updated = await api.getSettings();
    setSettingsData(updated);
  };

  const handleLogout = () => {
    removeStoredToken();
    setUser(null);
    setMessages([]);
    setSelectedDocId(null);
    setDocuments([]);
  };

  if (!authChecked) {
    return (
      <div className="auth-loading-screen">
        <div className="auth-spinner" style={{ width: '40px', height: '40px', borderWidth: '3px' }} />
      </div>
    );
  }

  if (!user) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />;
  }

  const selectedDoc = documents.find(d => d.id === selectedDocId);

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Navbar
        user={user}
        stats={stats}
        settingsData={settingsData}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Workspace */}
      <div className="main-content">
        <DocumentSidebar
          documents={documents}
          selectedDocId={selectedDocId}
          onSelectDoc={setSelectedDocId}
          onUpload={handleUpload}
          onDeleteDoc={handleDeleteDoc}
          onInspectChunks={handleInspectChunks}
          uploading={uploading}
          uploadError={uploadError}
        />

        <ChatInterface
          messages={messages}
          loading={loadingChat}
          onSendMessage={handleSendMessage}
          onClearChat={handleClearChat}
          onViewCitation={(cite) => setActiveCitation(cite)}
          selectedDoc={selectedDoc}
          documents={documents}
        />
      </div>

      {/* Citation Inspector Drawer */}
      <CitationDrawer
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settingsData}
        onSave={handleSaveSettings}
      />

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLogin={async (creds) => {
          const res = await api.login(creds.username, creds.password);
          setUser(res.user);
          await refreshDocuments();
        }}
        onRegister={async (creds) => {
          const res = await api.register(creds.username, creds.email, creds.password);
          setUser(res.user);
          await refreshDocuments();
        }}
        onGuestLogin={async () => {
          const res = await api.guestLogin();
          setUser(res.user);
          await refreshDocuments();
        }}
      />

      {/* Chunk Inspector Modal */}
      <ChunkInspectorModal
        isOpen={!!inspectorDoc}
        onClose={() => setInspectorDoc(null)}
        document={inspectorDoc}
        chunks={inspectorChunks}
        loading={loadingInspector}
      />
    </div>
  );
}
