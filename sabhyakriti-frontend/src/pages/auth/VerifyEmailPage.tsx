import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle, XCircle } from 'lucide-react';
import { verifyEmail } from '@/services/authService';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    if (!token) { setStatus('error'); return; }
    verifyEmail(token)
      .then(() => setStatus('success'))
      .catch(() => setStatus('error'));
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4" data-testid="verify-email-page">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-md p-8 text-center">
        {status === 'loading' && (
          <>
            <LoadingSpinner size="lg" className="mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900">Verifying your email...</h2>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle className="h-14 w-14 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Email Verified!</h2>
            <p className="text-sm text-gray-500 mb-6">Your email has been successfully verified. You can now sign in.</p>
            <Link to="/login" data-testid="verify-login-link" className="btn-primary">Sign In</Link>
          </>
        )}
        {status === 'error' && (
          <>
            <XCircle className="h-14 w-14 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Verification Failed</h2>
            <p className="text-sm text-gray-500 mb-6">The verification link is invalid or has expired.</p>
            <Link to="/login" className="btn-primary">Back to Sign In</Link>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;
