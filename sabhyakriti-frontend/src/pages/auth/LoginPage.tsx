import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, Smartphone } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { loginWithEmail, loginWithOTP } from '@/store/slices/authSlice';
import { sendOTP } from '@/services/authService';
import { isValidEmail, isValidIndianPhone, isValidOTP } from '@/utils/validation';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

type Tab = 'email' | 'otp';

const LoginPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, error } = useAppSelector((s) => s.auth);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/';
  const [tab, setTab] = useState<Tab>('email');

  // Email form
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // OTP form
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidEmail(email)) { toast.error('Enter a valid email'); return; }
    if (!password) { toast.error('Enter your password'); return; }
    const result = await dispatch(loginWithEmail({ email, password }));
    if (loginWithEmail.fulfilled.match(result)) {
      toast.success('Welcome back!');
      navigate(from, { replace: true });
    }
  };

  const handleSendOTP = async () => {
    if (!isValidIndianPhone(phone)) { toast.error('Enter a valid Indian phone number'); return; }
    setSendingOtp(true);
    try {
      await sendOTP(phone);
      setOtpSent(true);
      toast.success('OTP sent successfully');
    } catch {
      toast.error('Failed to send OTP');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleOTPLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidOTP(otp)) { toast.error('Enter valid 6-digit OTP'); return; }
    const result = await dispatch(loginWithOTP({ phone, otp }));
    if (loginWithOTP.fulfilled.match(result)) {
      toast.success('Welcome back!');
      navigate(from, { replace: true });
    }
  };

  const handleOAuth = (provider: 'google' | 'facebook') => {
    window.location.href = `/api/v1/auth/oauth/${provider}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4" data-testid="login-page">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-md p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Sign In</h1>
          <p className="text-sm text-gray-500 mt-1">Welcome back to Sabhyakriti</p>
        </div>

        {/* OAuth buttons */}
        <div className="space-y-2 mb-6">
          <button
            onClick={() => handleOAuth('google')}
            data-testid="google-login-btn"
            className="w-full flex items-center justify-center gap-3 py-2.5 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium"
          >
            <img src="https://www.google.com/favicon.ico" alt="Google" className="h-4 w-4" />
            Continue with Google
          </button>
          <button
            onClick={() => handleOAuth('facebook')}
            data-testid="facebook-login-btn"
            className="w-full flex items-center justify-center gap-3 py-2.5 bg-[#1877F2] text-white rounded-xl hover:bg-[#1666d0] transition-colors text-sm font-medium"
          >
            Continue with Facebook
          </button>
        </div>

        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
          <div className="relative flex justify-center"><span className="bg-white px-2 text-xs text-gray-400">or</span></div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-5">
          {(['email', 'otp'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              data-testid={`login-tab-${t}`}
              className={cn(
                'flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-sm font-medium transition-colors',
                tab === t ? 'bg-white text-saffron-600 shadow-sm' : 'text-gray-600'
              )}
            >
              {t === 'email' ? <Mail className="h-3.5 w-3.5" /> : <Smartphone className="h-3.5 w-3.5" />}
              {t === 'email' ? 'Email' : 'Phone OTP'}
            </button>
          ))}
        </div>

        {/* Email form */}
        {tab === 'email' && (
          <form onSubmit={handleEmailLogin} className="space-y-4" data-testid="email-login-form">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  data-testid="email-input"
                  className="input-field pl-9"
                  required
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-sm font-medium text-gray-700">Password</label>
                <Link to="/forgot-password" className="text-xs text-saffron-500 hover:text-saffron-600">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  data-testid="password-input"
                  className="input-field pl-9"
                  required
                />
              </div>
            </div>
            {error && <p className="text-xs text-red-500" data-testid="login-error">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              data-testid="email-login-submit"
              className="w-full btn-primary py-3"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        )}

        {/* OTP form */}
        {tab === 'otp' && (
          <form onSubmit={handleOTPLogin} className="space-y-4" data-testid="otp-login-form">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Mobile Number</label>
              <div className="flex gap-2">
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="9876543210"
                  data-testid="phone-input"
                  className="input-field flex-1"
                  disabled={otpSent}
                />
                <button
                  type="button"
                  onClick={handleSendOTP}
                  disabled={sendingOtp || otpSent}
                  data-testid="send-otp-btn"
                  className="px-3 py-2 bg-teal-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 whitespace-nowrap"
                >
                  {sendingOtp ? '...' : otpSent ? 'Sent' : 'Send OTP'}
                </button>
              </div>
            </div>
            {otpSent && (
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Enter OTP</label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="6-digit OTP"
                  data-testid="otp-input"
                  className="input-field text-center text-xl tracking-widest"
                  maxLength={6}
                />
              </div>
            )}
            <button
              type="submit"
              disabled={loading || !otpSent}
              data-testid="otp-login-submit"
              className="w-full btn-primary py-3 disabled:opacity-50"
            >
              {loading ? 'Verifying...' : 'Verify & Sign In'}
            </button>
          </form>
        )}

        <p className="text-center text-sm text-gray-500 mt-6">
          New to Sabhyakriti?{' '}
          <Link to="/register" className="text-saffron-500 hover:text-saffron-600 font-medium" data-testid="register-link">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
