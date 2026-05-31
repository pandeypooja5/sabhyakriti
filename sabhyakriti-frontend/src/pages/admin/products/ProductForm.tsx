import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Upload, X } from 'lucide-react';
import type { Product, Category } from '@/types';
import { createProduct, updateProduct, getProductById, listCategories, getPresignedUrl, confirmImageUpload } from '@/services/productService';
import axios from 'axios';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const ProductForm: React.FC = () => {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [uploadingImage, setUploadingImage] = useState(false);

  const [form, setForm] = useState({
    name: '', sku: '', description: '', mrp: '', price: '',
    stockQuantity: '', fabric: '', color: '', blouseIncluded: false,
    length: '', blouseLength: '', careInstructions: '', material: '',
    weaveType: '', isActive: true, isFeatured: false,
    fabricCategoryIds: [] as string[],
    occasionCategoryIds: [] as string[],
    regionCategoryIds: [] as string[],
  });
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [draftProductId, setDraftProductId] = useState<string | null>(null);

  useEffect(() => {
    listCategories().then(setCategories).catch(() => null);
    if (isEdit && id) {
      getProductById(id)
        .then((p: Product) => {
          setForm({
            name: p.name, sku: p.sku, description: p.description,
            mrp: String(p.mrp), price: String(p.price),
            stockQuantity: String(p.stockQuantity),
            fabric: p.fabric ?? '', color: p.color ?? '',
            blouseIncluded: p.blouseIncluded,
            length: p.length ? String(p.length) : '',
            blouseLength: p.blouseLength ? String(p.blouseLength) : '',
            careInstructions: p.careInstructions ?? '',
            material: p.material ?? '', weaveType: p.weaveType ?? '',
            isActive: p.isActive, isFeatured: p.isFeatured,
            fabricCategoryIds: p.fabricCategories.map((c) => c.id),
            occasionCategoryIds: p.occasionCategories.map((c) => c.id),
            regionCategoryIds: p.regionCategories.map((c) => c.id),
          });
          setImageUrls(p.images.map((img) => img.url));
        })
        .finally(() => setLoading(false));
    }
  }, [id, isEdit]);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // For new products, require at least name and SKU before uploading
    const productId = id ?? draftProductId;
    if (!productId) {
      if (!form.name.trim() || !form.sku.trim()) {
        toast.error('Please enter product Name and SKU before uploading images');
        return;
      }
      // Create a draft product so we have an ID for the presigned URL
      try {
        setSaving(true);
        const draft = await createProduct({
          name: form.name, sku: form.sku,
          description: form.description || form.name,
          mrp: Number(form.mrp) || 1,
          stockQuantity: Number(form.stockQuantity) || 0,
          isActive: false,
        });
        setDraftProductId(draft.id);
        setSaving(false);
        // Re-trigger with the new product id
        await uploadImage(file, draft.id);
        return;
      } catch {
        setSaving(false);
        toast.error('Could not create draft product for image upload');
        return;
      }
    }

    await uploadImage(file, productId);
  };

  const uploadImage = async (file: File, productId: string) => {
    setUploadingImage(true);
    try {
      // Use direct local upload endpoint — no S3 needed
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post(
        `/api/v1/products/${productId}/images/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${JSON.parse(localStorage.getItem('auth_tokens') || '{}').accessToken ?? ''}`,
          },
        },
      );
      const imageUrl: string = res.data.url;
      setImageUrls((prev) => [...prev, imageUrl]);
      toast.success('Image uploaded');
    } catch (err) {
      console.error('Image upload error:', err);
      toast.error('Image upload failed');
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.sku.trim()) { toast.error('Name and SKU are required'); return; }
    setSaving(true);
    try {
      const data = {
        ...form,
        mrp: Number(form.mrp),
        price: Number(form.price),
        stockQuantity: Number(form.stockQuantity),
        length: form.length ? Number(form.length) : undefined,
        blouseLength: form.blouseLength ? Number(form.blouseLength) : undefined,
      };
      if (isEdit && id) {
        await updateProduct(id, data);
        toast.success('Product updated');
      } else if (draftProductId) {
        // Draft was created during image upload — just update it with full data
        await updateProduct(draftProductId, { ...data, isActive: data.isActive });
        toast.success('Product created');
      } else {
        await createProduct(data);
        toast.success('Product created');
      }
      navigate('/admin/products');
    } catch {
      toast.error('Failed to save product');
    } finally {
      setSaving(false);
    }
  };

  const fabrics = categories.filter((c) => c.type === 'FABRIC');
  const occasions = categories.filter((c) => c.type === 'OCCASION');
  const regions = categories.filter((c) => c.type === 'REGION');

  const toggleCategory = (key: 'fabricCategoryIds' | 'occasionCategoryIds' | 'regionCategoryIds', id: string) => {
    setForm((f) => ({
      ...f,
      [key]: f[key].includes(id) ? f[key].filter((i) => i !== id) : [...f[key], id],
    }));
  };

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>;

  return (
    <div data-testid="product-form" className="max-w-3xl">
      <h1 className="text-xl font-bold text-gray-900 mb-6">{isEdit ? 'Edit Product' : 'Add New Product'}</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Basic Information</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="text-sm font-medium text-gray-700 mb-1 block">Product Name *</label>
              <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} data-testid="product-name-input" className="input-field" required />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">SKU *</label>
              <input value={form.sku} onChange={(e) => setForm((f) => ({ ...f, sku: e.target.value }))} data-testid="product-sku-input" className="input-field font-mono" required />
            </div>
            <div className="sm:col-span-2">
              <label className="text-sm font-medium text-gray-700 mb-1 block">Description</label>
              <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} rows={4} data-testid="product-desc-input" className="input-field resize-none" />
            </div>
          </div>
        </div>

        {/* Pricing */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Pricing & Inventory</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[['mrp', 'MRP (₹)'], ['price', 'Selling Price (₹)'], ['stockQuantity', 'Stock Qty']].map(([k, l]) => (
              <div key={k}>
                <label className="text-sm font-medium text-gray-700 mb-1 block">{l}</label>
                <input type="number" min="0" value={(form as Record<string, string>)[k]} onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))} data-testid={`product-${k}-input`} className="input-field" />
              </div>
            ))}
          </div>
        </div>

        {/* Attributes */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Product Attributes</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[['fabric', 'Fabric'], ['color', 'Color'], ['material', 'Material'], ['weaveType', 'Weave Type']].map(([k, l]) => (
              <div key={k}>
                <label className="text-sm font-medium text-gray-700 mb-1 block">{l}</label>
                <input value={(form as Record<string, string>)[k]} onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))} className="input-field" />
              </div>
            ))}
            {[['length', 'Length (m)'], ['blouseLength', 'Blouse Length (m)']].map(([k, l]) => (
              <div key={k}>
                <label className="text-sm font-medium text-gray-700 mb-1 block">{l}</label>
                <input type="number" step="0.1" value={(form as Record<string, string>)[k]} onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))} className="input-field" />
              </div>
            ))}
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.blouseIncluded} onChange={(e) => setForm((f) => ({ ...f, blouseIncluded: e.target.checked }))} className="h-4 w-4 text-saffron-500 rounded" />
              <span className="text-sm font-medium text-gray-700">Blouse Included</span>
            </label>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Care Instructions</label>
            <textarea value={form.careInstructions} onChange={(e) => setForm((f) => ({ ...f, careInstructions: e.target.value }))} rows={2} className="input-field resize-none" />
          </div>
        </div>

        {/* Categories */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Categories</h2>
          {[['Fabric', fabrics, 'fabricCategoryIds'], ['Occasion', occasions, 'occasionCategoryIds'], ['Region', regions, 'regionCategoryIds']].map(([title, cats, key]) => (
            <div key={key as string}>
              <label className="text-sm font-medium text-gray-700 mb-2 block">{title as string}</label>
              <div className="flex flex-wrap gap-2">
                {(cats as Category[]).map((cat) => (
                  <label key={cat.id} className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={(form[key as keyof typeof form] as string[]).includes(cat.id)}
                      onChange={() => toggleCategory(key as 'fabricCategoryIds' | 'occasionCategoryIds' | 'regionCategoryIds', cat.id)}
                      className="h-3.5 w-3.5 text-saffron-500 rounded"
                    />
                    <span className="text-sm text-gray-700">{cat.name}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Images */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Images</h2>
          <div className="flex flex-wrap gap-3">
            {imageUrls.map((url, idx) => (
              <div key={idx} className="relative h-20 w-20 rounded-lg overflow-hidden border border-gray-200">
                <img src={url} alt={`Product ${idx}`} className="h-full w-full object-cover" />
                <button
                  type="button"
                  onClick={() => setImageUrls((prev) => prev.filter((_, i) => i !== idx))}
                  className="absolute top-1 right-1 h-5 w-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
            <label className="h-20 w-20 rounded-lg border-2 border-dashed border-gray-300 flex flex-col items-center justify-center cursor-pointer hover:border-saffron-400 transition-colors">
              {uploadingImage ? <LoadingSpinner size="sm" /> : <Upload className="h-5 w-5 text-gray-400 mb-1" />}
              <span className="text-xs text-gray-400">Upload</span>
              <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" data-testid="image-upload-input" />
            </label>
          </div>
        </div>

        {/* Settings */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 flex gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.isActive} onChange={(e) => setForm((f) => ({ ...f, isActive: e.target.checked }))} className="h-4 w-4 text-saffron-500 rounded" data-testid="product-active-toggle" />
            <span className="text-sm font-medium text-gray-700">Active</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.isFeatured} onChange={(e) => setForm((f) => ({ ...f, isFeatured: e.target.checked }))} className="h-4 w-4 text-saffron-500 rounded" data-testid="product-featured-toggle" />
            <span className="text-sm font-medium text-gray-700">Featured</span>
          </label>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => navigate('/admin/products')}
            className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            data-testid="product-save-btn"
            className="flex-1 py-3 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold rounded-xl disabled:opacity-60"
          >
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Product'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProductForm;
