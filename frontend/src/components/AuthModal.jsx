import React, { useState } from 'react';
import { X, Lock, Mail, User, ArrowRight } from 'lucide-react';

export default function AuthModal({
  isOpen,
  onClose,
  onLogin,
  onRegister,
  onGuestLogin
}) {
  if (!isOpen) return null;

  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        if (!username || !email || !password) {
          setError('All fields are required.');
          return;
        }
        await onRegister({ username, email, password });
      } else {
        if (!username || !password) {
          setError('Please provide your username and password.');
          return;
        }
        await onLogin({ username, password });
      }
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = async () => {
    setError('');
    setLoading(true);
    try {
      await onGuestLogin();
      onClose();
    } catch (err) {
      setError('Guest login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '400px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">
            {isRegister ? 'Create an account' : 'Sign in to Folio'}
          </span>
          <button 
            className="btn-ghost" 
            style={{ padding: '0.25rem', borderRadius: '4px', cursor: 'pointer' }}
            onClick={onClose}
          >
            <X size={15} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div style={{ padding: '0.5rem 0.75rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '6px', color: '#fca5a5', fontSize: '0.78rem' }}>
                {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Username</label>
              <input 
                type="text"
                className="form-input"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            {isRegister && (
              <div className="form-group">
                <label className="form-label">Email</label>
                <input 
                  type="email"
                  className="form-input"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Password</label>
              <input 
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.25rem' }} disabled={loading}>
              <span>{isRegister ? 'Create account' : 'Sign in'}</span>
              <ArrowRight size={13} />
            </button>

            <div style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {isRegister ? (
                <>Already have an account? <span style={{ color: '#818cf8', cursor: 'pointer', fontWeight: 500 }} onClick={() => { setIsRegister(false); setError(''); }}>Sign in</span></>
              ) : (
                <>Don't have an account? <span style={{ color: '#818cf8', cursor: 'pointer', fontWeight: 500 }} onClick={() => { setIsRegister(true); setError(''); }}>Sign up</span></>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0.25rem 0' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }} />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-faint)' }}>or</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }} />
            </div>

            <button 
              type="button" 
              className="btn btn-secondary" 
              style={{ width: '100%' }}
              onClick={handleGuest}
              disabled={loading}
            >
              <span>Continue as Guest</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
