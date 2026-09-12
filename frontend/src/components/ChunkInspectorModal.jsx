import React from 'react';
import { X, Layers, Hash } from 'lucide-react';

export default function ChunkInspectorModal({
  isOpen,
  onClose,
  document,
  chunks,
  loading
}) {
  if (!isOpen || !document) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '640px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <Layers size={15} />
            <span>Passages: {document.filename}</span>
          </div>
          <button 
            className="btn-ghost" 
            style={{ padding: '0.25rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={onClose}
          >
            <X size={15} />
          </button>
        </div>

        <div className="modal-body" style={{ maxHeight: '60vh' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px', border: '1px solid var(--border-light)' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Total indexed passages: <strong>{chunks.length}</strong>
            </span>
            <span className="doc-badge">ChromaDB Store</span>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Loading passages...
            </div>
          ) : chunks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-faint)', fontSize: '0.8rem' }}>
              No passages found.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {chunks.map((item, idx) => {
                const meta = item.metadata || {};
                return (
                  <div key={idx} className="chunk-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <Hash size={11} />
                        <span>Passage #{meta.chunk_index !== undefined ? meta.chunk_index + 1 : idx + 1}</span>
                      </div>
                      <span className="doc-badge">Page {meta.page_number || 1} · {item.text?.length || 0} chars</span>
                    </div>
                    <div className="chunk-text">
                      {item.text}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
