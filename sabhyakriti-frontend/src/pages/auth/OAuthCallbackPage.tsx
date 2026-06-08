import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '@/store/store';
import { setCredentials } from '@/store/slices/authSlice';
import { getProfile } from '@/services/authService';
import type { AuthTokens } from '@/types';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';

/**
 * Lands here after the backend OAuth callback bounces the browser back with
 * tokens in the URL fragment: `/oauth/callback#access_token=...&refresh_token=...`
 * (or `#error=...`). Stores tokens, loads the profile, and signs the user in.
 */
const OAuthCallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return; // guard against React 18 double-invoke
    ran.current = true;

    const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const error = params.get('error');
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    const complete = async () => {
      if (error || !accessToken || !refreshToken) {
        toast.error('Google sign-in failed. Please try again.');
        navigate('/login', { replace: true });
        return;
      }

      const tokens: AuthTokens = { accessToken, refreshToken, expiresIn: 1800 };
      // Store first so apiClient attaches the token to the profile request.
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));
      // Strip tokens from the URL so they aren't left in browser history.
      window.history.replaceState(null, '', '/auth/callback');

      try {
        const user = await getProfile();
        dispatch(setCredentials({ user, tokens }));
        toast.success('Welcome!');
        navigate('/', { replace: true });
      } catch {
        localStorage.removeItem('auth_tokens');
        toast.error('Could not complete sign-in. Please try again.');
        navigate('/login', { replace: true });
      }
    };

    void complete();
  }, [navigate, dispatch]);

  return (
    <div className="min-h-screen flex items-center justify-center" data-testid="oauth-callback-page">
      <div className="text-center">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className="text-gray-600">Signing you in…</p>
      </div>
    </div>
  );
};

export default OAuthCallbackPage;
