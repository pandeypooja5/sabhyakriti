import { useState, useEffect } from 'react';
import { PlusCircle, MapPin } from 'lucide-react';
import type { Address } from '@/types';
import { listAddresses, addAddress } from '@/services/orderService';
import { isValidIndianPhone, isValidPincode } from '@/utils/validation';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface AddressStepProps {
  onNext: (addressId: string) => void;
}

const blankAddress: Omit<Address, 'id' | 'userId'> = {
  name: '', phone: '', line1: '', line2: '',
  city: '', state: '', pincode: '', country: 'India',
  isDefault: false, addressType: 'HOME',
};

const AddressStep: React.FC<AddressStepProps> = ({ onNext }) => {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(blankAddress);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof typeof blankAddress, string>>>({});

  useEffect(() => {
    listAddresses()
      .then((addrs) => {
        setAddresses(addrs);
        const def = addrs.find((a) => a.isDefault) ?? addrs[0];
        if (def) setSelected(def.id);
        if (addrs.length === 0) setShowForm(true);
      })
      .catch(() => setShowForm(true))
      .finally(() => setLoading(false));
  }, []);

  const validate = () => {
    const errs: typeof errors = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!isValidIndianPhone(form.phone)) errs.phone = 'Invalid phone number';
    if (!form.line1.trim()) errs.line1 = 'Address is required';
    if (!form.city.trim()) errs.city = 'City is required';
    if (!form.state.trim()) errs.state = 'State is required';
    if (!isValidPincode(form.pincode)) errs.pincode = 'Invalid PIN code';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSaveAddress = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const newAddr = await addAddress(form);
      setAddresses((prev) => [...prev, newAddr]);
      setSelected(newAddr.id);
      setShowForm(false);
      setForm(blankAddress);
      toast.success('Address saved successfully');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to save address');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="py-12 flex justify-center"><LoadingSpinner /></div>;

  return (
    <div data-testid="address-step">
      <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
        <MapPin className="h-5 w-5 text-saffron-500" /> Delivery Address
      </h2>

      {/* Address list */}
      {addresses.length > 0 && (
        <div className="space-y-3 mb-4">
          {addresses.map((addr) => (
            <label
              key={addr.id}
              className={cn(
                'flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors',
                selected === addr.id ? 'border-saffron-500 bg-saffron-50' : 'border-gray-200 hover:border-gray-300'
              )}
              data-testid={`address-option-${addr.id}`}
            >
              <input
                type="radio"
                name="address"
                value={addr.id}
                checked={selected === addr.id}
                onChange={() => setSelected(addr.id)}
                className="mt-1 text-saffron-500 focus:ring-saffron-500"
              />
              <div className="flex-1 text-sm">
                <p className="font-semibold text-gray-900">{addr.name}</p>
                <p className="text-gray-600">{addr.line1}{addr.line2 ? `, ${addr.line2}` : ''}</p>
                <p className="text-gray-600">{addr.city}, {addr.state} — {addr.pincode}</p>
                <p className="text-gray-500">{addr.phone}</p>
                {addr.isDefault && (
                  <span className="text-xs bg-teal-100 text-teal-700 px-1.5 py-0.5 rounded mt-1 inline-block">Default</span>
                )}
              </div>
            </label>
          ))}
        </div>
      )}

      {/* Add new address toggle */}
      {!showForm && (
        <button
          onClick={() => setShowForm(true)}
          data-testid="add-address-toggle"
          className="flex items-center gap-2 text-sm text-saffron-500 hover:text-saffron-600 font-medium mb-4"
        >
          <PlusCircle className="h-4 w-4" /> Add New Address
        </button>
      )}

      {/* Address Form */}
      {showForm && (
        <div className="bg-gray-50 rounded-xl p-4 mb-4 space-y-3" data-testid="add-address-form">
          <h3 className="font-semibold text-sm text-gray-800">New Address</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { key: 'name', placeholder: 'Full Name', label: 'Full Name', required: true },
              { key: 'phone', placeholder: '+91 98765 43210', label: 'Phone', required: true },
            ].map(({ key, placeholder, label }) => (
              <div key={key}>
                <label className="text-xs text-gray-600 mb-1 block">{label} *</label>
                <input
                  value={(form as Record<string, string>)[key]}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  data-testid={`address-${key}`}
                  className="input-field"
                />
                {errors[key as keyof typeof errors] && (
                  <p className="text-xs text-red-500 mt-0.5">{errors[key as keyof typeof errors]}</p>
                )}
              </div>
            ))}
          </div>
          <div>
            <label className="text-xs text-gray-600 mb-1 block">Address Line 1 *</label>
            <input
              value={form.line1}
              onChange={(e) => setForm((f) => ({ ...f, line1: e.target.value }))}
              placeholder="House/Flat No., Street"
              data-testid="address-line1"
              className="input-field"
            />
            {errors.line1 && <p className="text-xs text-red-500 mt-0.5">{errors.line1}</p>}
          </div>
          <input
            value={form.line2}
            onChange={(e) => setForm((f) => ({ ...f, line2: e.target.value }))}
            placeholder="Landmark (optional)"
            data-testid="address-line2"
            className="input-field"
          />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { key: 'city', placeholder: 'City' },
              { key: 'state', placeholder: 'State' },
              { key: 'pincode', placeholder: 'PIN Code' },
            ].map(({ key, placeholder }) => (
              <div key={key}>
                <input
                  value={(form as Record<string, string>)[key]}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  data-testid={`address-${key}`}
                  className="input-field"
                />
                {errors[key as keyof typeof errors] && (
                  <p className="text-xs text-red-500 mt-0.5">{errors[key as keyof typeof errors]}</p>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSaveAddress}
              disabled={saving}
              data-testid="save-address-btn"
              className="btn-primary text-sm py-2 px-4"
            >
              {saving ? 'Saving...' : 'Save Address'}
            </button>
            {addresses.length > 0 && (
              <button
                onClick={() => setShowForm(false)}
                className="text-sm text-gray-500 hover:text-gray-700 px-4"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      )}

      <button
        onClick={() => selected && onNext(selected)}
        disabled={!selected}
        data-testid="continue-to-payment-btn"
        className="w-full py-3 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Continue to Payment
      </button>
    </div>
  );
};

export default AddressStep;
