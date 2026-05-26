import { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, XCircle } from 'lucide-react';
import { bulkImport } from '@/services/productService';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

interface ImportResult {
  imported: number;
  failed: number;
  errors: string[];
}

const BulkImportPage: React.FC = () => {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const handleFile = (f: File) => {
    if (!f.name.endsWith('.csv')) { toast.error('Please upload a CSV file'); return; }
    setFile(f);
    setResult(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    try {
      const res = await bulkImport(file);
      setResult(res);
      if (res.failed === 0) toast.success(`Imported ${res.imported} products`);
      else toast(`Imported ${res.imported}, failed ${res.failed}`);
    } catch {
      toast.error('Import failed');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div data-testid="bulk-import-page" className="max-w-2xl">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Bulk Product Import</h1>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        data-testid="csv-drop-zone"
        className={cn(
          'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-colors',
          dragging ? 'border-saffron-400 bg-saffron-50' : 'border-gray-300 hover:border-gray-400'
        )}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          className="hidden"
          data-testid="csv-file-input"
        />
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileText className="h-8 w-8 text-saffron-500" />
            <div className="text-left">
              <p className="font-semibold text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
        ) : (
          <>
            <Upload className="h-10 w-10 text-gray-400 mx-auto mb-3" />
            <p className="font-medium text-gray-700">Drag & drop CSV file here</p>
            <p className="text-sm text-gray-400 mt-1">or click to browse</p>
          </>
        )}
      </div>

      {/* CSV format guide */}
      <div className="mt-4 p-4 bg-blue-50 rounded-xl text-sm text-blue-700">
        <p className="font-semibold mb-1">Required CSV columns:</p>
        <p className="font-mono text-xs">name, sku, mrp, price, stockQuantity, description, fabric, color</p>
      </div>

      {file && (
        <button
          onClick={handleImport}
          disabled={importing}
          data-testid="start-import-btn"
          className="mt-4 w-full py-3 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold rounded-xl disabled:opacity-60"
        >
          {importing ? 'Importing...' : 'Start Import'}
        </button>
      )}

      {/* Results */}
      {result && (
        <div className="mt-6 bg-white rounded-2xl border border-gray-100 p-5" data-testid="import-results">
          <div className="flex gap-4 mb-4">
            <div className="flex items-center gap-2 text-green-700">
              <CheckCircle className="h-5 w-5" />
              <span className="font-semibold">{result.imported} imported</span>
            </div>
            {result.failed > 0 && (
              <div className="flex items-center gap-2 text-red-600">
                <XCircle className="h-5 w-5" />
                <span className="font-semibold">{result.failed} failed</span>
              </div>
            )}
          </div>
          {result.errors.length > 0 && (
            <div className="space-y-1">
              <p className="text-sm font-semibold text-gray-700">Errors:</p>
              {result.errors.map((err, idx) => (
                <p key={idx} className="text-xs text-red-500 font-mono">{err}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BulkImportPage;
