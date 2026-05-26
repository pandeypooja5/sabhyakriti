import type { StockStatus } from '@/types';
import { cn } from '@/lib/utils';

interface StockBadgeProps {
  status: StockStatus;
  className?: string;
}

const config: Record<StockStatus, { label: string; classes: string }> = {
  IN_STOCK: { label: 'In Stock', classes: 'bg-green-100 text-green-800' },
  LOW_STOCK: { label: 'Low Stock', classes: 'bg-amber-100 text-amber-800' },
  OUT_OF_STOCK: { label: 'Out of Stock', classes: 'bg-red-100 text-red-700' },
};

const StockBadge: React.FC<StockBadgeProps> = ({ status, className }) => {
  const { label, classes } = config[status];
  return (
    <span
      data-testid="stock-badge"
      className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', classes, className)}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full mr-1.5', {
        'bg-green-500': status === 'IN_STOCK',
        'bg-amber-500': status === 'LOW_STOCK',
        'bg-red-500': status === 'OUT_OF_STOCK',
      })} />
      {label}
    </span>
  );
};

export default StockBadge;
