import { useState } from 'react';
import { useAppDispatch } from '@/store/store';
import { useAuth } from '@/hooks/useAuth';
import { updateProfile, changePassword } from '@/services/authService';
import { updateUser } from '@/store/slices/authSlice';
import toast from 'react-hot-toast';

const ProfileForm: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user } = useAuth();

  const [name, setName] = useState(user?.name ?? '');
  const [phone, setPhone] = useState(user?.phone ?? '');
  const [saving, setSaving] = useState(false);

  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [changingPwd, setChangingPwd] = useState(false);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateProfile({ name, phone });
      dispatch(updateUser(updated));
      toast.success('Profile updated');
    } catch {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPwd !== confirmPwd) { toast.error('Passwords do not match'); return; }
    if (newPwd.length < 8) { toast.error('Password must be at least 8 characters'); return; }
    setChangingPwd(true);
    try {
      await changePassword(currentPwd, newPwd);
      toast.success('Password changed successfully');
      setCurrentPwd(''); setNewPwd(''); setConfirmPwd('');
    } catch {
      toast.error('Failed to change password');
    } finally {
      setChangingPwd(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="profile-form">
      {/* Profile info */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h2 className="font-bold text-gray-900 mb-4">Personal Information</h2>
        <form onSubmit={handleProfileSave} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                data-testid="profile-name-input"
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Email</label>
              <input
                type="email"
                value={user?.email ?? ''}
                disabled
                className="input-field bg-gray-50 cursor-not-allowed"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Phone</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                data-testid="profile-phone-input"
                className="input-field"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={saving}
            data-testid="profile-save-btn"
            className="btn-primary py-2.5 px-6 text-sm"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Change password */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h2 className="font-bold text-gray-900 mb-4">Change Password</h2>
        <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
          {[
            { label: 'Current Password', value: currentPwd, setter: setCurrentPwd, testId: 'current-pwd-input' },
            { label: 'New Password', value: newPwd, setter: setNewPwd, testId: 'new-pwd-input' },
            { label: 'Confirm New Password', value: confirmPwd, setter: setConfirmPwd, testId: 'confirm-pwd-input' },
          ].map(({ label, value, setter, testId }) => (
            <div key={testId}>
              <label className="text-sm font-medium text-gray-700 mb-1 block">{label}</label>
              <input
                type="password"
                value={value}
                onChange={(e) => setter(e.target.value)}
                data-testid={testId}
                className="input-field"
                required
              />
            </div>
          ))}
          <button
            type="submit"
            disabled={changingPwd}
            data-testid="change-pwd-btn"
            className="btn-secondary py-2.5 px-6 text-sm"
          >
            {changingPwd ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ProfileForm;
