import { useState } from 'react';
import { Download } from 'lucide-react';
import { downloadInvoice } from '@/services/orderService';
import toast from 'react-hot-toast';

interface InvoiceDownloadButtonProps {
  orderId: string;
  orderNumber: string;
}

const InvoiceDownloadButton: React.FC<InvoiceDownloadButtonProps> = ({ orderId, orderNumber }) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const blob = await downloadInvoice(orderId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${orderNumber}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Failed to download invoice');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      data-testid="invoice-download-btn"
      className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-xl hover:bg-gray-50 disabled:opacity-50 transition-colors"
    >
      <Download className="h-4 w-4" />
      {loading ? 'Downloading...' : 'Download Invoice'}
    </button>
  );
};

export default InvoiceDownloadButton;
