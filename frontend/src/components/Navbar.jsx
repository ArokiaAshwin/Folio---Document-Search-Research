import React from 'react';
import { FileText, Sliders, LogIn, LogOut, Layers } from 'lucide-react';

export default function Navbar({
  user,
  stats,
  settingsData,
  onOpenSettings,
  onOpenAuth,
  onLogout
}) {
  const getUserInitials = (name) => {
    if (!name) return 'U';
    const parts = name.split(/[\s_]+/);
    if (parts.length > 1) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <header className="navbar">
      <div className="nav-brand">
        <div className="brand-icon-box">
          <FileText size={18} />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline' }}>
          <span className="brand-title">Folio</span>
          <span className="brand-subtitle">Document Search & Research</span>
        </div>
      </div>

      <div className="nav-actions">
        {/* Document chunk counter */}
        <div className="badge-counter" title="Indexed Knowledge Base">
          <Layers size={13} />
          <span>{stats?.total_chunks || 0} chunks</span>
        </div>

        {/* Engine status */}
        <div className="badge-counter">
          <span style={{ 
            width: 7, 
            height: 7, 
            borderRadius: '50%', 
            backgroundColor: settingsData?.has_gemini_key || settingsData?.has_openai_key ? '#10b981' : '#f59e0b' 
          }} />
          <span style={{ textTransform: 'capitalize' }}>
            {settingsData?.provider === 'gemini' ? 'Gemini' : 
             settingsData?.provider === 'openai' ? 'OpenAI' : 'Local search'}
          </span>
        </div>

        {/* Settings button */}
        <button 
          className="btn btn-secondary btn-sm" 
          onClick={onOpenSettings}
          title="Engine & Retrieval Settings"
        >
          <Sliders size={13} />
          <span>Settings</span>
        </button>

        {/* User Account */}
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div 
              className="badge-counter"
              style={{ fontWeight: 500, color: '#e0e7ff', gap: '0.45rem' }}
              title={`Logged in as ${user.username}`}
            >
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 20,
                height: 20,
                borderRadius: '50%',
                background: '#3730a3',
                fontSize: '0.65rem',
                fontWeight: 700
              }}>
                {getUserInitials(user.username)}
              </span>
              <span>{user.username}</span>
            </div>
            <button 
              className="btn btn-ghost btn-sm" 
              onClick={onLogout}
              title="Sign Out"
            >
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={onOpenAuth}>
            <LogIn size={13} />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
}
