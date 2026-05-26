import { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '@/services/authService';
import { isValidEmail } from '@/utils/validation';
import { Mail, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidEmail(email)) { toast.error('Enter a valid email'); return; }
    setLoading(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch {
      toast.error('Failed to send reset email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4" data-testid="forgot-password-page">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-md p-8">
        <Link to="/login" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft className="h-4 w-4" /> Back to Sign In
        </Link>

        {sent ? (
          <div className="text-center">
            <div className="h-14 w-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <Mail className="h-7 w-7 text-green-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Check your email</h2>
            <p className="text-sm text-gray-500">
              We've sent a password reset link to <strong>{email}</strong>. Check your inbox and follow the instructions.
            </p>
            <Link to="/login" className="btn-primary inline-block mt-6 text-sm">
              Back to Sign In
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Forgot Password?</h1>
            <p className="text-sm text-gray-500 mb-6">
              Enter your email and we'll send you a link to reset your password.
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  data-testid="forgot-email-input"
                  className="input-field"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                data-testid="forgot-submit-btn"
                className="w-full btn-primary py-3"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
