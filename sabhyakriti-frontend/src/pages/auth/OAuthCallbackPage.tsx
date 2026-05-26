import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAppDispatch } from '@/store/store';
import { loginWithOAuth } from '@/store/slices/authSlice';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';

const OAuthCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  useEffect(() => {
    const provider = searchParams.get('provider') ?? 'google';
    const code = searchParams.get('code') ?? '';

    if (!code) {
      toast.error('OAuth failed. Please try again.');
      navigate('/login', { replace: true });
      return;
    }

    dispatch(loginWithOAuth({ provider, code })).then((result) => {
      if (loginWithOAuth.fulfilled.match(result)) {
        toast.success('Signed in successfully!');
        navigate('/', { replace: true });
      } else {
        toast.error('OAuth sign-in failed');
        navigate('/login', { replace: true });
      }
    });
  }, [searchParams, dispatch, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center" data-testid="oauth-callback-page">
      <div className="text-center">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className="text-gray-600">Completing sign-in...</p>
      </div>
    </div>
  );
};

export default OAuthCallbackPage;
