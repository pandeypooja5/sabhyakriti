import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '@/services/authService';
import { useAppDispatch } from '@/store/store';
import { setCredentials } from '@/store/slices/authSlice';
import { isValidEmail, isValidIndianPhone, isStrongPassword } from '@/utils/validation';
import toast from 'react-hot-toast';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '', confirmPassword: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('Full name is required'); return; }
    if (!isValidEmail(form.email)) { toast.error('Enter a valid email'); return; }
    if (form.phone && !isValidIndianPhone(form.phone)) { toast.error('Enter a valid Indian phone number'); return; }
    if (!isStrongPassword(form.password)) { toast.error('Password must be 8+ chars with uppercase, lowercase, and digit'); return; }
    if (form.password !== form.confirmPassword) { toast.error('Passwords do not match'); return; }

    setLoading(true);
    try {
      const result = await register({ full_name: form.name, email: form.email, password: form.password });

      if ('tokens' in result && result.tokens) {
        // Dev mode: auto-logged in — save tokens and redirect to home
        localStorage.setItem('auth_tokens', JSON.stringify(result.tokens));
        localStorage.setItem('auth_user', JSON.stringify(result.user));
        dispatch(setCredentials({ user: result.user, tokens: result.tokens }));
        toast.success(`Welcome, ${result.user.name}! Account created.`);
        navigate('/');
      } else {
        toast.success('Account created! Please check your email to verify.');
        navigate('/login');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string; message?: string } } };
      toast.error(error.response?.data?.detail ?? error.response?.data?.message ?? 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: 'name', label: 'Full Name', type: 'text', placeholder: 'Your full name', required: true },
    { key: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com', required: true },
    { key: 'phone', label: 'Phone (optional)', type: 'tel', placeholder: '9876543210', required: false },
    { key: 'password', label: 'Password', type: 'password', placeholder: '8+ chars, upper, lower, digit', required: true },
    { key: 'confirmPassword', label: 'Confirm Password', type: 'password', placeholder: '••••••••', required: true },
  ] as const;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4" data-testid="register-page">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-md p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Create Account</h1>
          <p className="text-sm text-gray-500 mt-1">Join Sabhyakriti today</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {fields.map(({ key, label, type, placeholder, required }) => (
            <div key={key}>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                {label} {required && <span className="text-red-500">*</span>}
              </label>
              <input
                type={type}
                value={form[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                placeholder={placeholder}
                data-testid={`register-${key}`}
                required={required}
                className="input-field"
              />
            </div>
          ))}

          <button
            type="submit"
            disabled={loading}
            data-testid="register-submit"
            className="w-full btn-primary py-3 mt-2"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-saffron-500 hover:text-saffron-600 font-medium" data-testid="login-link">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
