import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { resetPassword } from '@/services/authService';
import { isStrongPassword } from '@/utils/validation';
import toast from 'react-hot-toast';

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) { toast.error('Invalid reset link'); return; }
    if (!isStrongPassword(password)) { toast.error('Password must be 8+ chars with uppercase, lowercase & digit'); return; }
    if (password !== confirm) { toast.error('Passwords do not match'); return; }
    setLoading(true);
    try {
      await resetPassword(token, password);
      toast.success('Password reset successfully. Please sign in.');
      navigate('/login');
    } catch {
      toast.error('Invalid or expired reset link');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center" data-testid="reset-password-invalid">
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-700 mb-2">Invalid Link</h2>
          <p className="text-gray-500 mb-4">This reset link is invalid or has expired.</p>
          <Link to="/forgot-password" className="btn-primary">Request New Link</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4" data-testid="reset-password-page">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-md p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Reset Password</h1>
        <p className="text-sm text-gray-500 mb-6">Enter your new password below.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">New Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} data-testid="new-password-input" className="input-field" required />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Confirm Password</label>
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} data-testid="confirm-password-input" className="input-field" required />
          </div>
          <button type="submit" disabled={loading} data-testid="reset-submit-btn" className="w-full btn-primary py-3">
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
