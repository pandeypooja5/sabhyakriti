import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { setPage } from '@/store/slices/productSlice';
import { cn } from '@/lib/utils';

const PLPPagination: React.FC = () => {
  const dispatch = useAppDispatch();
  const { page, totalPages } = useAppSelector((s) => s.products);

  if (totalPages <= 1) return null;

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  const visiblePages = pages.filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 2);

  const go = (p: number) => {
    dispatch(setPage(p));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <nav
      className="flex items-center justify-center gap-1 mt-8"
      aria-label="Pagination"
      data-testid="plp-pagination"
    >
      <button
        onClick={() => go(page - 1)}
        disabled={page <= 1}
        data-testid="pagination-prev"
        className={cn(
          'flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
          page <= 1
            ? 'text-gray-300 cursor-not-allowed'
            : 'text-gray-600 hover:bg-gray-100'
        )}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" /> Prev
      </button>

      {visiblePages.map((p, idx) => {
        const prev = visiblePages[idx - 1];
        const showEllipsis = prev !== undefined && p - prev > 1;
        return (
          <span key={p} className="flex items-center gap-1">
            {showEllipsis && <span className="px-1 text-gray-400 text-sm">…</span>}
            <button
              onClick={() => go(p)}
              data-testid={`pagination-page-${p}`}
              aria-current={p === page ? 'page' : undefined}
              className={cn(
                'h-8 w-8 rounded-lg text-sm font-medium transition-colors',
                p === page
                  ? 'bg-saffron-500 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              )}
            >
              {p}
            </button>
          </span>
        );
      })}

      <button
        onClick={() => go(page + 1)}
        disabled={page >= totalPages}
        data-testid="pagination-next"
        className={cn(
          'flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
          page >= totalPages
            ? 'text-gray-300 cursor-not-allowed'
            : 'text-gray-600 hover:bg-gray-100'
        )}
        aria-label="Next page"
      >
        Next <ChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
};

export default PLPPagination;
