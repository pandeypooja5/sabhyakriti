import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import type { Category } from '@/types';
import { listCategories } from '@/services/productService';
import apiClient from '@/services/apiClient';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const CategoryManager: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', type: 'FABRIC' as Category['type'], description: '' });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listCategories().then(setCategories).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!form.name.trim()) { toast.error('Name is required'); return; }
    setSaving(true);
    try {
      if (editingId) {
        const res = await apiClient.patch(`/admin/categories/${editingId}`, form);
        setCategories((prev) => prev.map((c) => c.id === editingId ? (res.data.category ?? res.data) : c));
        toast.success('Category updated');
      } else {
        const res = await apiClient.post('/admin/categories', form);
        setCategories((prev) => [...prev, res.data.category ?? res.data]);
        toast.success('Category created');
      }
      setShowForm(false); setEditingId(null); setForm({ name: '', type: 'FABRIC', description: '' });
    } catch {
      toast.error('Failed to save category');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await apiClient.delete(`/admin/categories/${id}`);
      setCategories((prev) => prev.filter((c) => c.id !== id));
      toast.success('Category deleted');
    } catch { toast.error('Failed to delete category'); }
  };

  const typeColors: Record<Category['type'], string> = {
    FABRIC: 'bg-orange-100 text-orange-700',
    OCCASION: 'bg-blue-100 text-blue-700',
    REGION: 'bg-green-100 text-green-700',
  };

  if (loading) return <div className="flex justify-center py-16"><LoadingSpinner /></div>;

  return (
    <div data-testid="category-manager">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Categories ({categories.length})</h1>
        <button
          onClick={() => { setShowForm(true); setEditingId(null); setForm({ name: '', type: 'FABRIC', description: '' }); }}
          data-testid="add-category-btn"
          className="flex items-center gap-1.5 px-4 py-2 bg-saffron-500 text-white text-sm font-medium rounded-xl hover:bg-saffron-600"
        >
          <Plus className="h-4 w-4" /> Add Category
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-2xl border border-gray-100 p-5 mb-4 space-y-3" data-testid="category-form">
          <h3 className="font-semibold text-gray-800">{editingId ? 'Edit Category' : 'New Category'}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Category name" className="input-field" data-testid="category-name-input" />
            <select value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value as Category['type'] }))} className="input-field" data-testid="category-type-select">
              <option value="FABRIC">Fabric</option>
              <option value="OCCASION">Occasion</option>
              <option value="REGION">Region</option>
            </select>
            <input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Description (optional)" className="input-field" />
          </div>
          <div className="flex gap-2">
            <button onClick={handleSave} disabled={saving} data-testid="category-save-btn" className="btn-primary text-sm py-2 px-4">
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button onClick={() => setShowForm(false)} className="text-sm text-gray-500 px-4">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Name</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Type</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Products</th>
              <th className="text-right px-4 py-3 font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {categories.map((cat) => (
              <tr key={cat.id} className="hover:bg-gray-50" data-testid="category-row">
                <td className="px-4 py-3 font-medium text-gray-900">{cat.name}</td>
                <td className="px-4 py-3">
                  <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium', typeColors[cat.type])}>
                    {cat.type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">{cat.productCount ?? '—'}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => { setForm({ name: cat.name, type: cat.type, description: cat.description ?? '' }); setEditingId(cat.id); setShowForm(true); }}
                      data-testid={`edit-cat-${cat.id}`}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"
                    ><Edit2 className="h-4 w-4" /></button>
                    <button
                      onClick={() => handleDelete(cat.id, cat.name)}
                      data-testid={`delete-cat-${cat.id}`}
                      className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg"
                    ><Trash2 className="h-4 w-4" /></button>
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

export default CategoryManager;
