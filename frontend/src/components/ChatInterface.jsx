import React, { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Download, BookOpen, Search, ArrowRight } from 'lucide-react';
import ChatMessage from './ChatMessage';

export default function ChatInterface({
  messages,
  loading,
  onSendMessage,
  onClearChat,
  onViewCitation,
  selectedDoc,
  documents
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaInput = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const exportChat = () => {
    if (messages.length === 0) return;
    const exportText = messages.map(m => `**${m.sender.toUpperCase()}:**\n${m.text}\n`).join('\n---\n\n');
    const blob = new Blob([exportText], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Document_Notes_${new Date().toISOString().slice(0,10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="chat-area">
      {/* Subheader */}
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
          <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>
            {selectedDoc ? selectedDoc.filename : 'All Documents'}
          </span>
          {selectedDoc ? (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
              (Filtered search)
            </span>
          ) : (
            <span style={{ color: 'var(--text-faint)', fontSize: '0.75rem' }}>
              · {documents.length} files in scope
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          {messages.length > 0 && (
            <>
              <button className="btn btn-ghost btn-sm" onClick={exportChat} title="Export to Markdown">
                <Download size={13} />
                <span>Export</span>
              </button>
              <button className="btn btn-ghost btn-sm" onClick={onClearChat} title="Clear conversation">
                <Trash2 size={13} />
                <span>Clear</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-icon-box">
              <BookOpen size={22} />
            </div>
            <h1 className="welcome-title">Search & Query Your Documents</h1>
            <p className="welcome-subtitle">
              Upload PDF reports, Word files, or notes on the left. Ask questions in natural language 
              to extract specific details, citations, and summaries.
            </p>

            <div className="suggested-prompts">
              <div 
                className="prompt-card"
                onClick={() => onSendMessage("What are the key points and executive summary of the document?")}
              >
                <div className="prompt-card-title">
                  <span>Executive Summary</span>
                  <ArrowRight size={12} color="#6366f1" />
                </div>
                <div className="prompt-card-desc">
                  Provide an overview of objectives and main findings.
                </div>
              </div>

              <div 
                className="prompt-card"
                onClick={() => onSendMessage("What are the important metrics, benchmarks, or figures mentioned?")}
              >
                <div className="prompt-card-title">
                  <span>Key Metrics & Figures</span>
                  <ArrowRight size={12} color="#6366f1" />
                </div>
                <div className="prompt-card-desc">
                  Extract factual statistics, percentages, and data points.
                </div>
              </div>

              <div 
                className="prompt-card"
                onClick={() => onSendMessage("Explain the core methodology, architecture, or procedure described.")}
              >
                <div className="prompt-card-title">
                  <span>Architecture & Process</span>
                  <ArrowRight size={12} color="#6366f1" />
                </div>
                <div className="prompt-card-desc">
                  Break down structural workflows and technical specs.
                </div>
              </div>

              <div 
                className="prompt-card"
                onClick={() => onSendMessage("Are there any restrictions, limitations, or future steps listed?")}
              >
                <div className="prompt-card-title">
                  <span>Next Steps & Risks</span>
                  <ArrowRight size={12} color="#6366f1" />
                </div>
                <div className="prompt-card-desc">
                  Identify dependencies, constraints, and recommendations.
                </div>
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <ChatMessage 
              key={index} 
              message={msg} 
              onViewCitation={onViewCitation} 
            />
          ))
        )}

        {loading && (
          <div className="message-row ai">
            <div className="avatar ai">AI</div>
            <div className="message-bubble ai" style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>Searching documents...</span>
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-container">
        <form className="input-box" onSubmit={handleSubmit}>
          <Search size={15} color="var(--text-faint)" />
          <textarea
            ref={textareaRef}
            rows={1}
            className="chat-input"
            placeholder={
              selectedDoc 
                ? `Ask a question about ${selectedDoc.filename}...` 
                : "Ask a question about your uploaded documents..."
            }
            value={input}
            onChange={handleTextareaInput}
            onKeyDown={handleKeyDown}
          />
          <button 
            type="submit" 
            className="send-btn" 
            disabled={!input.trim() || loading}
            title="Submit question"
          >
            <Send size={13} />
          </button>
        </form>
        <div style={{ textAlign: 'center', marginTop: '0.35rem', fontSize: '0.72rem', color: 'var(--text-faint)' }}>
          Press Enter to search, Shift+Enter for new line
        </div>
      </div>
    </main>
  );
}
