import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { socialAuth } from '../api';
import GigWayLoader from '../components/GigWayLoader';

const buildAuthError = (err) => {
    const data = err.response?.data;
    if (!data) {
        if (err.request) {
            return 'Backend did not respond. Check Vercel VITE_API_BASE_URL and Railway CORS settings.';
        }
        return err.message || 'Authentication failed';
    }
    if (typeof data === 'string') return data;
    if (data.error) return data.error;
    const firstField = Object.values(data).flat?.()[0];
    return firstField || 'Authentication failed';
};

const returnToLoginWithError = (message) => {
    sessionStorage.setItem('authError', message);
    window.location.replace('/login');
};

const GoogleCallback = () => {
    const navigate = useNavigate();
    const [error, setError] = useState(null);

    useEffect(() => {
        const handleAuth = async () => {
            try {
                // Extract access token from URL hash
                const hash = window.location.hash.substring(1);
                const params = new URLSearchParams(hash);
                const queryParams = new URLSearchParams(window.location.search);
                const accessToken = params.get('access_token');
                const authCode = queryParams.get('code');
                const errorParam = params.get('error') || queryParams.get('error');

                if (errorParam) {
                    returnToLoginWithError(`Google authentication failed: ${errorParam}`);
                    return;
                }

                if (!accessToken && !authCode) {
                    returnToLoginWithError('No Google credentials were received. Check the authorized redirect URI in Google Cloud.');
                    return;
                }

                // Send token to backend
                const data = authCode
                    ? await socialAuth('google', null, null, {
                        code: authCode,
                        redirect_uri: `${window.location.origin}/auth/google/callback`
                    })
                    : await socialAuth('google', accessToken);
                
                if (data.token) {
                    localStorage.setItem('token', data.token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    // Redirect to dashboard or return location
                    const storedReturnPath = localStorage.getItem('socialAuthReturn');
                    const returnPath = storedReturnPath && !['/login', '/register', '/auth/google/callback'].includes(storedReturnPath)
                        ? storedReturnPath
                        : '/dashboard';
                    localStorage.removeItem('socialAuthReturn');
                    window.location.replace(returnPath);
                } else {
                    returnToLoginWithError('Google authentication failed: backend did not return a token.');
                }
            } catch (err) {
                console.error('Google authentication failed', err);
                returnToLoginWithError(buildAuthError(err));
            }
        };

        handleAuth();
    }, [navigate]);

    return (
        <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center', 
            minHeight: '100vh',
            color: 'var(--text-primary)'
        }}>
            {error ? (
                <>
                    <p style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</p>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Redirecting to login...</p>
                </>
            ) : (
                <GigWayLoader label="Processing Google login" compact />
            )}
        </div>
    );
};

export default GoogleCallback;
