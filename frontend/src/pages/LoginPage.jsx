import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { login, socialAuth } from '../api';
import '../styles/Auth.css';

const buildAuthError = (err, fallback) => {
    const data = err.response?.data;
    if (!data) return fallback;
    if (typeof data === 'string') return data;
    if (data.error) return data.error;
    if (data.non_field_errors?.length) return data.non_field_errors[0];
    const firstField = Object.values(data).flat?.()[0];
    return firstField || fallback;
};

const LoginPage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });

    useEffect(() => {
        if (localStorage.getItem('token')) {
            navigate('/dashboard', { replace: true });
            return;
        }

        if (location.state?.message) {
            setSuccessMsg(location.state.message);
        }
    }, [location, navigate]);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        setError(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        setSuccessMsg(null);

        try {
            const data = await login(formData.email, formData.password);

            // Save token
            if (data.token) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));

                // Redirect to dashboard
                navigate('/dashboard');
            } else {
                setError("Login failed: No token received");
            }
        } catch (err) {
            setError(buildAuthError(err, "Invalid credentials"));
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
            if (!clientId) {
                setError("Google OAuth not configured. Please set VITE_GOOGLE_CLIENT_ID");
                setIsLoading(false);
                return;
            }

            // Return to a real app page after auth. Do not bounce back to auth pages.
            const currentPath = window.location.pathname;
            const returnPath = ['/login', '/register', '/auth/google/callback'].includes(currentPath)
                ? '/dashboard'
                : currentPath;
            localStorage.setItem('socialAuthReturn', returnPath);

            // Use Google OAuth2 redirect flow
            const redirectUri = `${window.location.origin}/auth/google/callback`;
            const scope = 'openid email profile';
            const responseType = 'code';

            const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
                `client_id=${clientId}&` +
                `redirect_uri=${encodeURIComponent(redirectUri)}&` +
                `response_type=${responseType}&` +
                `scope=${encodeURIComponent(scope)}&` +
                `access_type=offline&` +
                `prompt=select_account`;

            // Redirect to Google OAuth
            window.location.href = authUrl;

        } catch (err) {
            setError("Failed to initialize Google login");
            setIsLoading(false);
        }
    };

    const handleFacebookLogin = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const appId = import.meta.env.VITE_FACEBOOK_APP_ID;
            if (!appId) {
                setError("Facebook OAuth not configured. Please set VITE_FACEBOOK_APP_ID");
                setIsLoading(false);
                return;
            }

            // Load Facebook SDK if not already loaded
            if (!window.FB) {
                window.fbAsyncInit = function () {
                    window.FB.init({
                        appId: appId,
                        cookie: true,
                        xfbml: true,
                        version: 'v18.0'
                    });
                };

                const script = document.createElement('script');
                script.src = 'https://connect.facebook.net/en_US/sdk.js';
                script.async = true;
                script.defer = true;
                document.head.appendChild(script);

                await new Promise((resolve) => {
                    const checkFB = setInterval(() => {
                        if (window.FB) {
                            clearInterval(checkFB);
                            resolve();
                        }
                    }, 100);
                    // Timeout after 5 seconds
                    setTimeout(() => {
                        clearInterval(checkFB);
                        resolve();
                    }, 5000);
                });
            }

            if (!window.FB) {
                throw new Error("Failed to load Facebook SDK");
            }

            // Request Facebook login
            window.FB.login(async (response) => {
                if (response.authResponse) {
                    try {
                        const data = await socialAuth('facebook', response.authResponse.accessToken);

                        if (data.token) {
                            localStorage.setItem('token', data.token);
                            localStorage.setItem('user', JSON.stringify(data.user));
                            navigate('/dashboard');
                        }
                    } catch (err) {
                        setError(buildAuthError(err, "Facebook login failed"));
                        setIsLoading(false);
                    }
                } else {
                    setError("Facebook login was cancelled");
                    setIsLoading(false);
                }
            }, { scope: 'email,public_profile' });
        } catch (err) {
            setError(err.message || "Failed to initialize Facebook login");
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-container login-page">
            <div className="auth-card">
                <h2 className="auth-title">Welcome Back</h2>
                <p className="auth-subtitle">Log in to manage your gigs</p>

                {error && <div className="error-msg">{error}</div>}
                {successMsg && <div className="error-msg" style={{ borderColor: 'var(--primary)', backgroundColor: 'var(--primary-glow)', color: 'white' }}>{successMsg}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <input
                            type="email"
                            name="email"
                            className="form-input"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            placeholder="you@example.com"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            name="password"
                            className="form-input"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            placeholder="••••••••"
                        />
                    </div>

                    <button type="submit" className="btn btn-primary auth-btn" disabled={isLoading}>
                        {isLoading ? <Loader2 className="animate-spin mx-auto" size={20} /> : "Log In"}
                    </button>
                </form>

                <div style={{ margin: '1.5rem 0', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }}></div>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>OR</span>
                    <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }}></div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <button
                        type="button"
                        onClick={handleGoogleLogin}
                        disabled={isLoading}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            borderRadius: '0.5rem',
                            border: '1px solid rgba(255,255,255,0.1)',
                            background: 'rgba(255,255,255,0.05)',
                            color: 'var(--text-primary)',
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem',
                            fontSize: '0.95rem',
                            fontWeight: '500',
                            transition: 'all 0.2s ease'
                        }}
                        onMouseOver={(e) => !isLoading && (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
                        onMouseOut={(e) => !isLoading && (e.currentTarget.style.background = 'rgba(255,255,255,0.05)')}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                        </svg>
                        Continue with Google
                    </button>

                    <button
                        type="button"
                        onClick={handleFacebookLogin}
                        disabled={isLoading}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            borderRadius: '0.5rem',
                            border: '1px solid rgba(255,255,255,0.1)',
                            background: 'rgba(255,255,255,0.05)',
                            color: 'var(--text-primary)',
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '0.5rem',
                            fontSize: '0.95rem',
                            fontWeight: '500',
                            transition: 'all 0.2s ease'
                        }}
                        onMouseOver={(e) => !isLoading && (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
                        onMouseOut={(e) => !isLoading && (e.currentTarget.style.background = 'rgba(255,255,255,0.05)')}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="#1877F2">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                        </svg>
                        Continue with Facebook
                    </button>
                </div>

                <div className="auth-footer">
                    Don't have an account?
                    <Link to="/register" className="auth-link">Sign Up</Link>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
