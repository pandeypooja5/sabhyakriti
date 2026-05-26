import { cn } from '@/lib/utils';
import { PackageOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message?: string;
  ctaLabel?: string;
  ctaHref?: string;
  onCtaClick?: () => void;
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  message,
  ctaLabel,
  ctaHref,
  onCtaClick,
  className,
}) => {
  return (
    <div
      data-testid="empty-state"
      className={cn(
        'flex flex-col items-center justify-center py-16 px-4 text-center',
        className
      )}
    >
      <div className="mb-4 text-gray-300">
        {icon ?? <PackageOpen className="h-16 w-16" />}
      </div>
      <h3 className="text-lg font-semibold text-gray-700 mb-2">{title}</h3>
      {message && <p className="text-sm text-gray-500 max-w-xs mb-6">{message}</p>}
      {ctaLabel && ctaHref && (
        <Link
          to={ctaHref}
          data-testid="empty-state-cta"
          className="btn-primary inline-flex items-center gap-2"
        >
          {ctaLabel}
        </Link>
      )}
      {ctaLabel && onCtaClick && !ctaHref && (
        <button
          onClick={onCtaClick}
          data-testid="empty-state-cta"
          className="btn-primary"
        >
          {ctaLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
