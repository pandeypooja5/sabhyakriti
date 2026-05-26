import { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import type { Product } from '@/types';
import { listInventory, updateStock } from '@/services/adminService';
import StockBadge from '@/components/shared/StockBadge';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';

const InventoryManager: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [edits, setEdits] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    listInventory(page)
      .then((res) => { setProducts(res.data); setTotal(res.total); })
      .catch(() => null)
      .finally(() => setLoading(false));
  }, [page]);

  const handleSaveStock = async (productId: string) => {
    const newQty = edits[productId];
    if (newQty === undefined) return;
    setSaving(productId);
    try {
      const updated = await updateStock(productId, newQty);
      setProducts((prev) => prev.map((p) => p.id === productId ? updated : p));
      setEdits((prev) => { const next = { ...prev }; delete next[productId]; return next; });
      toast.success('Stock updated');
    } catch {
      toast.error('Failed to update stock');
    } finally {
      setSaving(null);
    }
  };

  return (
    <div data-testid="inventory-manager">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Inventory ({total})</h1>

      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><LoadingSpinner /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Product</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">SKU</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Current Stock</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Status</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">New Qty</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Save</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {products.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50" data-testid="inventory-row">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <img src={product.images[0]?.url ?? '/placeholder.jpg'} alt={product.name} className="h-8 w-8 rounded object-cover" />
                        <span className="font-medium text-gray-900 line-clamp-1 max-w-[180px]">{product.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{product.sku}</td>
                    <td className="px-4 py-3 text-center font-bold">{product.stockQuantity}</td>
                    <td className="px-4 py-3 text-center"><StockBadge status={product.stockStatus} /></td>
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        value={edits[product.id] ?? ''}
                        onChange={(e) => setEdits((prev) => ({ ...prev, [product.id]: Number(e.target.value) }))}
                        placeholder={String(product.stockQuantity)}
                        data-testid={`stock-input-${product.id}`}
                        className="w-20 text-center input-field text-sm"
                      />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleSaveStock(product.id)}
                        disabled={edits[product.id] === undefined || saving === product.id}
                        data-testid={`save-stock-${product.id}`}
                        className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg disabled:opacity-40 transition-colors"
                        aria-label="Save stock"
                      >
                        {saving === product.id ? '...' : <Save className="h-4 w-4" />}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {total > 20 && (
        <div className="flex justify-center gap-2 mt-4">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40">Prev</button>
          <span className="px-3 py-1.5 text-sm text-gray-500">Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 text-sm border rounded-lg">Next</button>
        </div>
      )}
    </div>
  );
};

export default InventoryManager;
