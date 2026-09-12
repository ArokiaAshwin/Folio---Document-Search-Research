import React, { useState } from 'react';
import { X, Sliders, Check, Eye, EyeOff } from 'lucide-react';

export default function SettingsModal({
  isOpen,
  onClose,
  settings,
  onSave
}) {
  if (!isOpen) return null;

  const [provider, setProvider] = useState(settings?.provider || 'gemini');
  const [model, setModel] = useState(settings?.model || 'gemini-2.0-flash');
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [chunkSize, setChunkSize] = useState(settings?.chunk_size || 1000);
  const [topK, setTopK] = useState(settings?.top_k || 4);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        provider,
        model,
        chunk_size: parseInt(chunkSize, 10),
        top_k: parseInt(topK, 10)
      };
      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
      if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim();

      await onSave(payload);
      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 700);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <Sliders size={15} />
            <span>Search & Model Settings</span>
          </div>
          <button 
            className="btn-ghost" 
            style={{ padding: '0.25rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={onClose}
          >
            <X size={15} />
          </button>
        </div>

        <form onSubmit={handleSave}>
          <div className="modal-body">
            {/* Model Provider */}
            <div className="form-group">
              <label className="form-label">Model Provider</label>
              <select 
                className="form-select"
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value);
                  if (e.target.value === 'gemini') setModel('gemini-2.0-flash');
                  if (e.target.value === 'openai') setModel('gpt-4o-mini');
                }}
              >
                <option value="gemini">Google Gemini</option>
                <option value="openai">OpenAI</option>
                <option value="extractive">Local Search (No API key needed)</option>
              </select>
            </div>

            {/* Model Choice */}
            {provider !== 'extractive' && (
              <div className="form-group">
                <label className="form-label">Model</label>
                <select 
                  className="form-select"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                >
                  {provider === 'gemini' ? (
                    <>
                      <option value="gemini-2.0-flash">gemini-2.0-flash (Fast)</option>
                      <option value="gemini-1.5-pro">gemini-1.5-pro (Accurate)</option>
                      <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                    </>
                  ) : (
                    <>
                      <option value="gpt-4o-mini">gpt-4o-mini</option>
                      <option value="gpt-4o">gpt-4o</option>
                    </>
                  )}
                </select>
              </div>
            )}

            {/* API Key */}
            {provider === 'gemini' && (
              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <label className="form-label">Gemini API Key</label>
                  {settings?.has_gemini_key && (
                    <span style={{ fontSize: '0.72rem', color: '#10b981' }}>Saved</span>
                  )}
                </div>
                <div style={{ position: 'relative' }}>
                  <input 
                    type={showGeminiKey ? 'text' : 'password'}
                    className="form-input"
                    style={{ width: '100%', paddingRight: '2.2rem' }}
                    placeholder={settings?.has_gemini_key ? "••••••••••••••••" : "Paste API key..."}
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                  />
                  <button 
                    type="button" 
                    className="btn-ghost" 
                    style={{ position: 'absolute', right: '0.3rem', top: '50%', transform: 'translateY(-50%)', padding: '0.2rem' }}
                    onClick={() => setShowGeminiKey(!showGeminiKey)}
                  >
                    {showGeminiKey ? <EyeOff size={13} /> : <Eye size={13} />}
                  </button>
                </div>
              </div>
            )}

            {provider === 'openai' && (
              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <label className="form-label">OpenAI API Key</label>
                  {settings?.has_openai_key && (
                    <span style={{ fontSize: '0.72rem', color: '#10b981' }}>Saved</span>
                  )}
                </div>
                <div style={{ position: 'relative' }}>
                  <input 
                    type={showOpenaiKey ? 'text' : 'password'}
                    className="form-input"
                    style={{ width: '100%', paddingRight: '2.2rem' }}
                    placeholder={settings?.has_openai_key ? "••••••••••••••••" : "sk-..."}
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                  />
                  <button 
                    type="button" 
                    className="btn-ghost" 
                    style={{ position: 'absolute', right: '0.3rem', top: '50%', transform: 'translateY(-50%)', padding: '0.2rem' }}
                    onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                  >
                    {showOpenaiKey ? <EyeOff size={13} /> : <Eye size={13} />}
                  </button>
                </div>
              </div>
            )}

            {/* Retrieval Options */}
            <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '0.85rem' }}>
              <div className="form-group" style={{ marginBottom: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <label className="form-label">Passages to retrieve (Top-K)</label>
                  <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{topK}</span>
                </div>
                <input 
                  type="range" 
                  min="1" 
                  max="8" 
                  value={topK}
                  onChange={(e) => setTopK(e.target.value)}
                  style={{ accentColor: 'var(--primary)', cursor: 'pointer' }}
                />
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <label className="form-label">Chunk size (chars)</label>
                  <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{chunkSize}</span>
                </div>
                <input 
                  type="range" 
                  min="400" 
                  max="1500" 
                  step="100"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(e.target.value)}
                  style={{ accentColor: 'var(--primary)', cursor: 'pointer' }}
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary btn-sm" disabled={saving}>
              {savedSuccess ? (
                <>
                  <Check size={13} />
                  <span>Saved</span>
                </>
              ) : (
                <span>Save</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
