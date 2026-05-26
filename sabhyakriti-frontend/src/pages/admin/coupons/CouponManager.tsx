import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import type { Coupon } from '@/types';
import { listCoupons, createCoupon, updateCoupon, deleteCoupon } from '@/services/adminService';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import { formatDate as fDate } from '@/utils/date';

const blankForm: Omit<Coupon, 'id' | 'usedCount' | 'createdAt'> = {
  code: '', description: '', discountType: 'PERCENT', discountValue: 10,
  minOrderValue: undefined, maxDiscountAmount: undefined,
  usageLimit: undefined, isActive: true, expiresAt: undefined,
};

const CouponManager: React.FC = () => {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(blankForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listCoupons().then(setCoupons).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!form.code.trim()) { toast.error('Code is required'); return; }
    setSaving(true);
    try {
      if (editingId) {
        const updated = await updateCoupon(editingId, form);
        setCoupons((prev) => prev.map((c) => c.id === editingId ? updated : c));
        toast.success('Coupon updated');
      } else {
        const created = await createCoupon(form);
        setCoupons((prev) => [...prev, created]);
        toast.success('Coupon created');
      }
      setShowForm(false); setEditingId(null); setForm(blankForm);
    } catch { toast.error('Failed to save coupon'); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id: string, code: string) => {
    if (!confirm(`Delete coupon "${code}"?`)) return;
    try {
      await deleteCoupon(id);
      setCoupons((prev) => prev.filter((c) => c.id !== id));
      toast.success('Coupon deleted');
    } catch { toast.error('Failed to delete coupon'); }
  };

  if (loading) return <div className="flex justify-center py-16"><LoadingSpinner /></div>;

  return (
    <div data-testid="coupon-manager">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Coupons ({coupons.length})</h1>
        <button
          onClick={() => { setShowForm(true); setEditingId(null); setForm(blankForm); }}
          data-testid="add-coupon-btn"
          className="flex items-center gap-1.5 px-4 py-2 bg-saffron-500 text-white text-sm font-medium rounded-xl hover:bg-saffron-600"
        >
          <Plus className="h-4 w-4" /> Add Coupon
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-2xl border border-gray-100 p-5 mb-4 space-y-3" data-testid="coupon-form">
          <h3 className="font-semibold text-gray-800">{editingId ? 'Edit Coupon' : 'New Coupon'}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))} placeholder="COUPON CODE *" className="input-field uppercase font-mono" data-testid="coupon-code-field" />
            <input value={form.description ?? ''} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Description" className="input-field" />
            <select value={form.discountType} onChange={(e) => setForm((f) => ({ ...f, discountType: e.target.value as 'PERCENT' | 'FLAT' }))} className="input-field" data-testid="coupon-type-select">
              <option value="PERCENT">Percentage (%)</option>
              <option value="FLAT">Flat Amount (₹)</option>
            </select>
            <input type="number" value={form.discountValue} onChange={(e) => setForm((f) => ({ ...f, discountValue: Number(e.target.value) }))} placeholder={form.discountType === 'PERCENT' ? 'Discount %' : 'Discount ₹'} className="input-field" data-testid="coupon-value-field" />
            <input type="number" value={form.minOrderValue ?? ''} onChange={(e) => setForm((f) => ({ ...f, minOrderValue: e.target.value ? Number(e.target.value) : undefined }))} placeholder="Min Order Value (₹)" className="input-field" />
            <input type="number" value={form.maxDiscountAmount ?? ''} onChange={(e) => setForm((f) => ({ ...f, maxDiscountAmount: e.target.value ? Number(e.target.value) : undefined }))} placeholder="Max Discount Cap (₹)" className="input-field" />
            <input type="number" value={form.usageLimit ?? ''} onChange={(e) => setForm((f) => ({ ...f, usageLimit: e.target.value ? Number(e.target.value) : undefined }))} placeholder="Usage Limit" className="input-field" />
            <input type="date" value={form.expiresAt ?? ''} onChange={(e) => setForm((f) => ({ ...f, expiresAt: e.target.value || undefined }))} className="input-field" />
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.isActive} onChange={(e) => setForm((f) => ({ ...f, isActive: e.target.checked }))} className="h-4 w-4 text-saffron-500 rounded" />
            <span className="text-sm text-gray-700">Active</span>
          </label>
          <div className="flex gap-2">
            <button onClick={handleSave} disabled={saving} data-testid="coupon-save-btn" className="btn-primary text-sm py-2 px-4">{saving ? 'Saving...' : 'Save'}</button>
            <button onClick={() => setShowForm(false)} className="text-sm text-gray-500 px-4">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {['Code', 'Type', 'Value', 'Used', 'Expires', 'Active', 'Actions'].map((h) => (
                <th key={h} className="text-left px-4 py-3 font-semibold text-gray-600">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {coupons.map((coupon) => (
              <tr key={coupon.id} className="hover:bg-gray-50" data-testid="coupon-row">
                <td className="px-4 py-3 font-mono font-bold text-teal-700">{coupon.code}</td>
                <td className="px-4 py-3 text-gray-600">{coupon.discountType}</td>
                <td className="px-4 py-3 font-semibold">
                  {coupon.discountType === 'PERCENT' ? `${coupon.discountValue}%` : `₹${coupon.discountValue}`}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {coupon.usedCount}{coupon.usageLimit ? `/${coupon.usageLimit}` : ''}
                </td>
                <td className="px-4 py-3 text-gray-500">{coupon.expiresAt ? fDate(coupon.expiresAt) : '—'}</td>
                <td className="px-4 py-3">
                  <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', coupon.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500')}>
                    {coupon.isActive ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    <button onClick={() => { setForm({ code: coupon.code, description: coupon.description, discountType: coupon.discountType, discountValue: coupon.discountValue, minOrderValue: coupon.minOrderValue, maxDiscountAmount: coupon.maxDiscountAmount, usageLimit: coupon.usageLimit, isActive: coupon.isActive, expiresAt: coupon.expiresAt }); setEditingId(coupon.id); setShowForm(true); }} data-testid={`edit-coupon-${coupon.id}`} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"><Edit2 className="h-4 w-4" /></button>
                    <button onClick={() => handleDelete(coupon.id, coupon.code)} data-testid={`delete-coupon-${coupon.id}`} className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CouponManager;
