import React, { useState, useRef } from 'react';
import { 
  Upload, FileText, Trash2, Eye, Loader2, Plus, 
  AlertCircle, FileSpreadsheet, FileCode, File
} from 'lucide-react';

export default function DocumentSidebar({
  documents,
  selectedDocId,
  onSelectDoc,
  onUpload,
  onDeleteDoc,
  onInspectChunks,
  uploading,
  uploadError
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files);
      e.target.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (filename) => {
    const ext = filename?.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return <FileText size={15} color="#ef4444" />;
    if (ext === 'docx' || ext === 'doc') return <FileText size={15} color="#3b82f6" />;
    if (ext === 'csv') return <FileSpreadsheet size={15} color="#10b981" />;
    if (ext === 'md' || ext === 'json') return <FileCode size={15} color="#f59e0b" />;
    return <File size={15} color="var(--text-muted)" />;
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Documents</span>
        <button 
          className="btn btn-secondary btn-sm"
          onClick={() => fileInputRef.current?.click()}
          title="Upload document"
        >
          <Plus size={13} />
          <span>Add</span>
        </button>
      </div>

      {/* Upload Zone */}
      <div 
        className={`dropzone ${isDragOver ? 'active' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          multiple 
          accept=".pdf,.docx,.doc,.txt,.md,.csv,.json"
          onChange={handleFileChange}
        />
        {uploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
            <Loader2 className="dropzone-icon animate-spin" size={20} />
            <span className="dropzone-text">Indexing file...</span>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Upload className="dropzone-icon" size={20} />
            <span className="dropzone-text">Upload documents</span>
            <span className="dropzone-hint">PDF, DOCX, TXT, Markdown</span>
          </div>
        )}
      </div>

      {uploadError && (
        <div style={{ margin: '0 1.25rem 0.5rem', padding: '0.5rem 0.75rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '6px', fontSize: '0.75rem', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <AlertCircle size={13} flexShrink={0} />
          <span>{uploadError}</span>
        </div>
      )}

      {selectedDocId && (
        <div style={{ margin: '0 1.25rem 0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255, 255, 255, 0.04)', padding: '0.35rem 0.65rem', borderRadius: '4px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          <span>Filtered to 1 file</span>
          <button 
            style={{ background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', fontSize: '0.72rem' }}
            onClick={() => onSelectDoc(null)}
          >
            Reset
          </button>
        </div>
      )}

      {/* Document List */}
      <div className="document-list">
        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-faint)', fontSize: '0.8rem' }}>
            No documents uploaded yet.
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocId === doc.id;
            return (
              <div 
                key={doc.id}
                className={`document-item ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectDoc(isSelected ? null : doc.id)}
              >
                <div className="doc-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', overflow: 'hidden' }}>
                    {getFileIcon(doc.filename)}
                    <span className="doc-name" title={doc.filename}>{doc.filename}</span>
                  </div>
                  <span className="doc-badge">
                    {doc.filename?.split('.').pop()?.toUpperCase()}
                  </span>
                </div>

                <div className="doc-meta">
                  <span>{doc.total_chunks || 0} passages · {formatFileSize(doc.size_bytes)}</span>
                  
                  <div style={{ display: 'flex', gap: '0.25rem' }} onClick={(e) => e.stopPropagation()}>
                    <button 
                      className="btn-ghost" 
                      style={{ padding: '0.2rem', borderRadius: '4px', cursor: 'pointer' }}
                      title="Inspect chunks"
                      onClick={() => onInspectChunks(doc)}
                    >
                      <Eye size={12} />
                    </button>
                    <button 
                      className="btn-ghost" 
                      style={{ padding: '0.2rem', borderRadius: '4px', cursor: 'pointer', color: '#ef4444' }}
                      title="Delete file"
                      onClick={() => onDeleteDoc(doc.id, doc.filename)}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
