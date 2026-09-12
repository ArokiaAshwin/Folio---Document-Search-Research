import React, { useState } from 'react';
import { Copy, Check, FileText } from 'lucide-react';

export default function ChatMessage({ message, onViewCitation }) {
  const [copied, setCopied] = useState(false);
  const isAi = message.sender === 'ai';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatMarkdown = (content) => {
    if (!content) return null;
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('### ')) {
        return <h3 key={idx}>{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx}>{line.replace('## ', '')}</h2>;
      }
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        const text = line.trim().substring(2);
        return (
          <li key={idx} dangerouslySetInnerHTML={{ __html: parseInlineStyles(text) }} />
        );
      }
      const numMatch = line.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        return (
          <li key={idx} dangerouslySetInnerHTML={{ __html: parseInlineStyles(numMatch[2]) }} />
        );
      }
      if (line.startsWith('> ')) {
        return (
          <blockquote key={idx} dangerouslySetInnerHTML={{ __html: parseInlineStyles(line.replace('> ', '')) }} />
        );
      }
      if (!line.trim()) {
        return <div key={idx} style={{ height: '0.4rem' }} />;
      }
      return (
        <p key={idx} dangerouslySetInnerHTML={{ __html: parseInlineStyles(line) }} />
      );
    });
  };

  const parseInlineStyles = (text) => {
    let parsed = text;
    parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    parsed = parsed.replace(/\*(.*?)\*/g, '<em>$1</em>');
    parsed = parsed.replace(/`([^`]+)`/g, '<code>$1</code>');
    return parsed;
  };

  return (
    <div className={`message-row ${message.sender}`}>
      <div className={`avatar ${message.sender}`}>
        {isAi ? 'AI' : 'YOU'}
      </div>

      <div className={`message-bubble ${message.sender}`}>
        <div className="markdown-body">
          {formatMarkdown(message.text)}
        </div>

        {/* Citations / Source References */}
        {isAi && message.citations && message.citations.length > 0 && (
          <div className="citations-wrapper">
            <div className="citations-header">
              <FileText size={12} />
              <span>Referenced Sources</span>
            </div>
            <div className="citations-grid">
              {message.citations.map((cite, i) => (
                <button
                  key={i}
                  className="citation-chip"
                  onClick={() => onViewCitation(cite)}
                  title="Click to view source passage in inspector"
                >
                  <span>{cite.filename}</span>
                  <span style={{ color: 'var(--text-faint)' }}>· p. {cite.page_number}</span>
                  {cite.similarity_score !== undefined && (
                    <span className="score-badge">
                      {Math.round(cite.similarity_score * 100)}%
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Footer info */}
        {isAi && (
          <div className="message-footer">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              {message.model && <span>{message.model}</span>}
              {message.latency_ms !== undefined && <span>{message.latency_ms}ms</span>}
            </div>

            <button 
              className="btn-ghost" 
              style={{ padding: '0.15rem 0.4rem', fontSize: '0.72rem', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
              onClick={handleCopy}
              title="Copy to clipboard"
            >
              {copied ? <Check size={11} color="#10b981" /> : <Copy size={11} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
