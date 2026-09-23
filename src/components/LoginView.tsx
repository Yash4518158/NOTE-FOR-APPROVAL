import React, { useState, useEffect } from 'react';
import type { AuthMode, User, LoginResponse } from '../types';
import { ShieldCheck, User as UserIcon, Lock, AlertCircle, Building, Loader2, Eye, EyeOff } from 'lucide-react';

interface LoginViewProps {
  onLoginSuccess: (user: User, token: string) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [authMode, setAuthMode] = useState<AuthMode>('LOCAL');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('Password123!');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch Admin-configured Auth Mode from Backend Environment Config (.env)
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/auth/config')
      .then((res) => res.json())
      .then((data) => {
        if (data.isSuccess && data.auth_mode) {
          setAuthMode(data.auth_mode as AuthMode);
          if (data.auth_mode === 'AD') {
            setUsername('admin_ad');
          } else {
            setUsername('admin');
          }
        }
      })
      .catch(() => {
        // Fallback to LOCAL default
      });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username.trim(),
          password: password,
          auth_mode: authMode,
        }),
      });

      const data: LoginResponse = await response.json();

      if (response.ok && data.isSuccess && data.user && data.token) {
        onLoginSuccess(data.user, data.token);
      } else {
        setErrorMsg(data.message || 'Login failed. Please check your credentials.');
      }
    } catch (err) {
      setErrorMsg('Network error. Unable to connect to Backend API server at http://127.0.0.1:8000');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="brand-header">
          <div className="brand-icon">
            <ShieldCheck size={28} />
          </div>
          <h1 className="brand-title">NFA Workflow System</h1>
          <p className="brand-subtitle">Enterprise Note for Approval Management Portal</p>
        </div>

        {errorMsg && (
          <div className="alert-box alert-error">
            <AlertCircle size={18} />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">
              {authMode === 'LOCAL' ? 'Username / Email' : 'Active Directory User Alias'}
            </label>
            <div className="input-wrapper">
              <UserIcon className="input-icon" size={18} />
              <input
                type="text"
                className="form-input"
                placeholder={authMode === 'LOCAL' ? 'Enter username or email (e.g. admin, buyer, approver1)' : 'Enter AD Alias (e.g. admin_ad)'}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              {authMode === 'LOCAL' ? 'Password' : 'Active Directory Password'}
            </label>
            <div className="input-wrapper" style={{ position: 'relative' }}>
              <Lock className="input-icon" size={18} />
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                style={{ paddingRight: '44px' }}
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
                title={showPassword ? 'Hide Password' : 'Show Password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <Loader2 size={18} /> Verifying Credentials...
              </span>
            ) : (
              'Sign In to NFA Portal'
            )}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '12px', color: '#94a3b8' }}>
          <Building size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
          Admin Security Mode: <strong style={{ color: '#475569' }}>{authMode === 'LOCAL' ? 'Local Database (.env)' : 'Active Directory (.env)'}</strong>
        </div>
      </div>
    </div>
  );
};
