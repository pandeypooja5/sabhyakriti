import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Edit2, Trash2, Upload } from 'lucide-react';
import type { Product } from '@/types';
import { listProducts, deleteProduct } from '@/services/productService';
import { formatINR } from '@/utils/currency';
import StockBadge from '@/components/shared/StockBadge';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';

const ProductManager: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await listProducts({ search: search || undefined, page, pageSize: 20 });
      setProducts(res.data);
      setTotal(res.total);
    } catch {
      toast.error('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, search]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await deleteProduct(id);
      toast.success('Product deleted');
      fetchData();
    } catch {
      toast.error('Failed to delete product');
    }
  };

  return (
    <div data-testid="product-manager">
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <h1 className="text-xl font-bold text-gray-900">Products ({total})</h1>
        <div className="flex gap-2">
          <Link
            to="/admin/products/bulk-import"
            className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-xl hover:bg-gray-50"
            data-testid="bulk-import-btn"
          >
            <Upload className="h-4 w-4" /> Import CSV
          </Link>
          <Link
            to="/admin/products/new"
            className="flex items-center gap-1.5 px-4 py-2 bg-saffron-500 text-white text-sm font-medium rounded-xl hover:bg-saffron-600"
            data-testid="add-product-btn"
          >
            <Plus className="h-4 w-4" /> Add Product
          </Link>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-4 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search products..."
          data-testid="product-search"
          className="input-field pl-9"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><LoadingSpinner /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Product</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">SKU</th>
                  <th className="text-right px-4 py-3 font-semibold text-gray-600">Price</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Stock</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Status</th>
                  <th className="text-right px-4 py-3 font-semibold text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {products.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50" data-testid="product-row">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <img
                          src={product.images[0]?.url ?? '/placeholder.jpg'}
                          alt={product.name}
                          className="h-10 w-10 rounded-lg object-cover flex-shrink-0"
                        />
                        <span className="font-medium text-gray-900 line-clamp-1 max-w-[200px]">{product.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">{product.sku}</td>
                    <td className="px-4 py-3 text-right font-semibold">{formatINR(product.price)}</td>
                    <td className="px-4 py-3 text-center">{product.stockQuantity}</td>
                    <td className="px-4 py-3 text-center"><StockBadge status={product.stockStatus} /></td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/admin/products/${product.id}/edit`}
                          data-testid={`edit-product-${product.id}`}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          aria-label="Edit product"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => handleDelete(product.id, product.name)}
                          data-testid={`delete-product-${product.id}`}
                          className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          aria-label="Delete product"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex justify-center gap-2 mt-4">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40">Prev</button>
          <span className="px-3 py-1.5 text-sm text-gray-500">Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg">Next</button>
        </div>
      )}
    </div>
  );
};

export default ProductManager;
