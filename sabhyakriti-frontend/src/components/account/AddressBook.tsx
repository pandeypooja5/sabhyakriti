import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Star } from 'lucide-react';
import type { Address } from '@/types';
import { listAddresses, addAddress, updateAddress, deleteAddress, setDefaultAddress } from '@/services/orderService';
import { isValidIndianPhone, isValidPincode } from '@/utils/validation';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const blankForm: Omit<Address, 'id' | 'userId'> = {
  name: '', phone: '', line1: '', line2: '',
  city: '', state: '', pincode: '', country: 'India',
  isDefault: false, addressType: 'HOME',
};

const AddressBook: React.FC = () => {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [form, setForm] = useState(blankForm);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listAddresses()
      .then(setAddresses)
      .finally(() => setLoading(false));
  }, []);

  const validate = () => {
    if (!form.name.trim()) { toast.error('Name is required'); return false; }
    if (!isValidIndianPhone(form.phone)) { toast.error('Invalid phone number'); return false; }
    if (!form.line1.trim()) { toast.error('Address line 1 is required'); return false; }
    if (!form.city.trim()) { toast.error('City is required'); return false; }
    if (!form.state.trim()) { toast.error('State is required'); return false; }
    if (!isValidPincode(form.pincode)) { toast.error('Invalid PIN code'); return false; }
    return true;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      if (editingId) {
        const updated = await updateAddress(editingId, form);
        setAddresses((prev) => prev.map((a) => a.id === editingId ? updated : a));
        toast.success('Address updated');
      } else {
        const newAddr = await addAddress(form);
        setAddresses((prev) => [...prev, newAddr]);
        toast.success('Address added');
      }
      setShowAddForm(false);
      setEditingId(null);
      setForm(blankForm);
    } catch {
      toast.error('Failed to save address');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this address?')) return;
    try {
      await deleteAddress(id);
      setAddresses((prev) => prev.filter((a) => a.id !== id));
      toast.success('Address deleted');
    } catch {
      toast.error('Failed to delete address');
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await setDefaultAddress(id);
      setAddresses((prev) => prev.map((a) => ({ ...a, isDefault: a.id === id })));
      toast.success('Default address updated');
    } catch {
      toast.error('Failed to update default address');
    }
  };

  const startEdit = (addr: Address) => {
    setForm({ name: addr.name, phone: addr.phone, line1: addr.line1, line2: addr.line2 ?? '', city: addr.city, state: addr.state, pincode: addr.pincode, country: addr.country, isDefault: addr.isDefault, addressType: addr.addressType });
    setEditingId(addr.id);
    setShowAddForm(true);
  };

  if (loading) return <div className="flex justify-center py-10"><LoadingSpinner /></div>;

  return (
    <div data-testid="address-book">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-bold text-gray-900">Saved Addresses</h2>
        <button
          onClick={() => { setShowAddForm(true); setEditingId(null); setForm(blankForm); }}
          data-testid="add-address-btn"
          className="flex items-center gap-1.5 text-sm text-saffron-500 hover:text-saffron-600 font-medium"
        >
          <Plus className="h-4 w-4" /> Add Address
        </button>
      </div>

      {/* Address cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        {addresses.map((addr) => (
          <div
            key={addr.id}
            className={cn('relative p-4 rounded-xl border-2 transition-colors', addr.isDefault ? 'border-saffron-400 bg-saffron-50' : 'border-gray-200 bg-white')}
            data-testid={`address-card-${addr.id}`}
          >
            {addr.isDefault && (
              <span className="absolute top-3 right-3 text-xs bg-saffron-100 text-saffron-600 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                <Star className="h-3 w-3 fill-current" /> Default
              </span>
            )}
            <p className="font-semibold text-sm text-gray-900">{addr.name}</p>
            <p className="text-sm text-gray-600 mt-0.5">{addr.line1}{addr.line2 ? `, ${addr.line2}` : ''}</p>
            <p className="text-sm text-gray-600">{addr.city}, {addr.state} — {addr.pincode}</p>
            <p className="text-xs text-gray-500 mt-0.5">{addr.phone}</p>
            <div className="flex gap-2 mt-3">
              <button onClick={() => startEdit(addr)} data-testid={`edit-address-${addr.id}`} className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
                <Edit2 className="h-3 w-3" /> Edit
              </button>
              <button onClick={() => handleDelete(addr.id)} data-testid={`delete-address-${addr.id}`} className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1">
                <Trash2 className="h-3 w-3" /> Delete
              </button>
              {!addr.isDefault && (
                <button onClick={() => handleSetDefault(addr.id)} data-testid={`set-default-${addr.id}`} className="text-xs text-saffron-500 hover:text-saffron-700 ml-auto flex items-center gap-1">
                  <Star className="h-3 w-3" /> Set Default
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add/Edit form */}
      {showAddForm && (
        <div className="bg-gray-50 rounded-xl p-4 space-y-3" data-testid="address-form">
          <h3 className="font-semibold text-sm text-gray-800">{editingId ? 'Edit Address' : 'New Address'}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {([['name', 'Full Name'], ['phone', 'Phone']] as [keyof typeof form, string][]).map(([key, placeholder]) => (
              <input key={key} value={(form as Record<string, string>)[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} placeholder={placeholder} className="input-field" />
            ))}
          </div>
          <input value={form.line1} onChange={(e) => setForm((f) => ({ ...f, line1: e.target.value }))} placeholder="Address Line 1" className="input-field" />
          <input value={form.line2} onChange={(e) => setForm((f) => ({ ...f, line2: e.target.value }))} placeholder="Landmark (optional)" className="input-field" />
          <div className="grid grid-cols-3 gap-3">
            {([['city', 'City'], ['state', 'State'], ['pincode', 'PIN Code']] as [keyof typeof form, string][]).map(([key, placeholder]) => (
              <input key={key} value={(form as Record<string, string>)[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} placeholder={placeholder} className="input-field" />
            ))}
          </div>
          <div className="flex gap-2">
            <button onClick={handleSave} disabled={saving} data-testid="address-save-btn" className="btn-primary text-sm py-2 px-4">
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button onClick={() => { setShowAddForm(false); setEditingId(null); }} className="text-sm text-gray-500 hover:text-gray-700 px-4">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AddressBook;
