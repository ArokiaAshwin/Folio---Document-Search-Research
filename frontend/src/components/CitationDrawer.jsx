import React from 'react';
import { X, FileText } from 'lucide-react';

export default function CitationDrawer({ citation, onClose }) {
  if (!citation) return null;

  const scorePercent = citation.similarity_score 
    ? Math.round(citation.similarity_score * 100) 
    : null;

  return (
    <div className="drawer">
      <div className="drawer-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <FileText size={16} color="#818cf8" />
          <h3 style={{ fontSize: '0.9rem', fontWeight: 600 }}>Source Reference</h3>
        </div>
        <button 
          className="btn-ghost" 
          style={{ padding: '0.3rem', borderRadius: '4px', cursor: 'pointer' }}
          onClick={onClose}
        >
          <X size={16} />
        </button>
      </div>

      <div className="drawer-content">
        <div className="chunk-card" style={{ borderColor: 'var(--border-medium)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.85rem' }}>
              {citation.filename || 'Document'}
            </span>
            <span className="doc-badge">Page {citation.page_number || 1}</span>
          </div>

          {scorePercent !== null && (
            <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              <span>Relevance Score</span>
              <span style={{ fontWeight: 600, color: '#818cf8' }}>{scorePercent}%</span>
            </div>
          )}

          {citation.chunk_id && (
            <div style={{ marginTop: '0.4rem', fontSize: '0.68rem', color: 'var(--text-faint)', fontFamily: 'var(--font-mono)' }}>
              Ref: {citation.chunk_id}
            </div>
          )}
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '0.4rem' }}>
            Extracted Passage
          </span>
          <div className="chunk-card">
            <div className="chunk-text">
              {citation.snippet || citation.text || 'No passage text available.'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
