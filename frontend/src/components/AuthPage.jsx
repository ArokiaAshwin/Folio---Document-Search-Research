import React, { useState, useEffect, useRef } from 'react';
import { Mail, Lock, Eye, EyeOff, ArrowRight, CheckCircle2, AlertCircle, Sparkles, BookOpen, Search, ShieldCheck } from 'lucide-react';
import { api } from '../api';

export default function AuthPage({ onAuthSuccess }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState('');
  const [googleScriptReady, setGoogleScriptReady] = useState(false);

  const googleBtnRef = useRef(null);

  // Fetch auth config on mount
  useEffect(() => {
    let mounted = true;
    api.getAuthConfig()
      .then(config => {
        if (mounted && config?.google_client_id) {
          setGoogleClientId(config.google_client_id);
        }
      })
      .catch(() => {});

    // Check if Google script is loaded
    const checkGoogle = setInterval(() => {
      if (window.google?.accounts?.id) {
        setGoogleScriptReady(true);
        clearInterval(checkGoogle);
      }
    }, 200);

    return () => {
      mounted = false;
      clearInterval(checkGoogle);
    };
  }, []);

  // Initialize official Google Identity Services button if Client ID exists
  useEffect(() => {
    if (googleScriptReady && googleClientId && googleBtnRef.current) {
      try {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response) => {
            if (response.credential) {
              setLoading(true);
              setError('');
              try {
                const res = await api.googleLogin(response.credential);
                onAuthSuccess(res.user);
              } catch (err) {
                setError(err.message || 'Google sign-in failed');
              } finally {
                setLoading(false);
              }
            }
          }
        });

        window.google.accounts.id.renderButton(googleBtnRef.current, {
          theme: 'outline',
          size: 'large',
          width: '360',
          text: isSignUp ? 'signup_with' : 'signin_with',
          shape: 'rectangular',
          logo_alignment: 'left'
        });
      } catch (e) {
        console.error('Google button init error:', e);
      }
    }
  }, [googleScriptReady, googleClientId, isSignUp]);

  const handleCustomGoogleClick = async () => {
    // If client ID is set and Google prompt can be shown
    if (googleClientId && window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
      return;
    }

    // Interactive Demo Google Sign-In for instant preview without requiring immediate GCP setup
    setLoading(true);
    setError('');
    try {
      const demoToken = `demo_google:researcher@company.com:Alex Chen`;
      const res = await api.googleLogin(demoToken);
      onAuthSuccess(res.user);
    } catch (err) {
      setError(err.message || 'Google authentication demo failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setError('Please enter your email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    if (isSignUp) {
      if (password.length < 6) {
        setError('Password must be at least 6 characters long.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match. Please re-enter.');
        return;
      }

      setLoading(true);
      try {
        const res = await api.register(cleanEmail, password);
        setSuccessMsg('Account created successfully! Welcome to Folio.');
        setTimeout(() => {
          onAuthSuccess(res.user);
        }, 500);
      } catch (err) {
        setError(err.message || 'Registration failed. Please try another email.');
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(true);
      try {
        const res = await api.login(cleanEmail, password);
        onAuthSuccess(res.user);
      } catch (err) {
        setError(err.message || 'Invalid email or password.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleGuestLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await api.guestLogin();
      onAuthSuccess(res.user);
    } catch (err) {
      setError('Guest login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;
  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword;

  return (
    <div className="auth-page-wrapper">
      {/* Background glow effects */}
      <div className="auth-bg-glow-1" />
      <div className="auth-bg-glow-2" />

      <div className="auth-card-container">
        {/* Brand Header */}
        <div className="auth-header">
          <div className="auth-brand-badge">
            <div className="auth-brand-icon">
              <BookOpen size={20} className="text-indigo-400" />
            </div>
            <span className="auth-brand-name">Folio</span>
          </div>
          <h1 className="auth-title">
            {isSignUp ? 'Create your account' : 'Sign in to Folio'}
          </h1>
          <p className="auth-subtitle">
            {isSignUp
              ? 'Join to research, query and extract insights from documents'
              : 'Search internal documents, technical specs, and PDFs'}
          </p>
        </div>

        {/* Auth Form Card */}
        <div className="auth-card">
          {/* Notifications */}
          {error && (
            <div className="auth-alert auth-alert-error">
              <AlertCircle size={16} className="auth-alert-icon" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="auth-alert auth-alert-success">
              <CheckCircle2 size={16} className="auth-alert-icon" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form">
            {/* Email Field */}
            <div className="auth-input-group">
              <label className="auth-label">Email Address</label>
              <div className="auth-input-wrapper">
                <Mail size={16} className="auth-input-icon" />
                <input
                  type="email"
                  className="auth-input"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="auth-input-group">
              <div className="auth-label-row">
                <label className="auth-label">Password</label>
                {isSignUp && (
                  <span className="auth-hint">Min. 6 characters</span>
                )}
              </div>
              <div className="auth-input-wrapper">
                <Lock size={16} className="auth-input-icon" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={isSignUp ? 'new-password' : 'current-password'}
                  required
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Confirm Password Field (Sign Up Only) */}
            {isSignUp && (
              <div className="auth-input-group">
                <div className="auth-label-row">
                  <label className="auth-label">Confirm Password</label>
                  {passwordsMatch && (
                    <span className="auth-validation-success">
                      <CheckCircle2 size={12} /> Passwords match
                    </span>
                  )}
                  {passwordsMismatch && (
                    <span className="auth-validation-error">
                      Passwords do not match
                    </span>
                  )}
                </div>
                <div className="auth-input-wrapper">
                  <Lock size={16} className="auth-input-icon" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    className={`auth-input ${passwordsMismatch ? 'auth-input-error' : ''}`}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    className="auth-password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                    title={showConfirmPassword ? 'Hide password' : 'Show password'}
                  >
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            )}

            {/* Primary Submit Button */}
            <button
              type="submit"
              className="auth-btn-primary"
              disabled={loading}
            >
              {loading ? (
                <div className="auth-spinner" />
              ) : (
                <>
                  <span>{isSignUp ? 'Create Account' : 'Sign In'}</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="auth-divider">
            <div className="auth-divider-line" />
            <span className="auth-divider-text">or continue with</span>
            <div className="auth-divider-line" />
          </div>

          {/* Google Sign-In */}
          <div className="auth-social-box">
            {googleClientId ? (
              <div ref={googleBtnRef} className="auth-google-gis-container" />
            ) : (
              <button
                type="button"
                className="auth-btn-google"
                onClick={handleCustomGoogleClick}
                disabled={loading}
              >
                <svg className="auth-google-icon" viewBox="0 0 24 24" width="18" height="18">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>{isSignUp ? 'Sign up with Google' : 'Sign in with Google'}</span>
              </button>
            )}
          </div>

          {/* Toggle View (Sign In vs Sign Up) */}
          <div className="auth-footer-toggle">
            {isSignUp ? (
              <p>
                Already have an account?{' '}
                <button
                  type="button"
                  className="auth-link"
                  onClick={() => {
                    setIsSignUp(false);
                    setError('');
                    setSuccessMsg('');
                  }}
                >
                  Sign in
                </button>
              </p>
            ) : (
              <p>
                Don't have an account?{' '}
                <button
                  type="button"
                  className="auth-link"
                  onClick={() => {
                    setIsSignUp(true);
                    setError('');
                    setSuccessMsg('');
                  }}
                >
                  Sign up
                </button>
              </p>
            )}
          </div>
        </div>

        {/* Guest Demo Preview */}
        <div className="auth-guest-option">
          <span>Need a quick test? </span>
          <button
            type="button"
            className="auth-guest-link"
            onClick={handleGuestLogin}
            disabled={loading}
          >
            Explore workspace as Guest
          </button>
        </div>

        {/* Feature Highlights Footer */}
        <div className="auth-features-row">
          <div className="auth-feature-item">
            <Search size={14} className="text-indigo-400" />
            <span>Hybrid Neural Search</span>
          </div>
          <div className="auth-feature-item">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span>Verifiable Grounded Citations</span>
          </div>
          <div className="auth-feature-item">
            <Sparkles size={14} className="text-amber-400" />
            <span>Gemini & OpenAI Support</span>
          </div>
        </div>
      </div>
    </div>
  );
}
