import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns';

const safeParse = (dateStr?: string | null): Date | null => {
  if (!dateStr) return null;
  const d = parseISO(dateStr);
  return isValid(d) ? d : null;
};

/**
 * Format date as "14 Jan 2025"
 */
export const formatDate = (dateStr?: string | null): string => {
  const d = safeParse(dateStr);
  return d ? format(d, 'd MMM yyyy') : '—';
};

/**
 * Format date-time as "14 Jan 2025, 3:45 PM"
 */
export const formatDateTime = (dateStr?: string | null): string => {
  const d = safeParse(dateStr);
  return d ? format(d, 'd MMM yyyy, h:mm a') : '—';
};

/**
 * Returns relative time e.g. "2 hours ago", "3 days ago"
 */
export const timeAgo = (dateStr?: string | null): string => {
  const d = safeParse(dateStr);
  return d ? formatDistanceToNow(d, { addSuffix: true }) : '—';
};

/**
 * Format for input[type=date] value: "2025-01-14"
 */
export const formatDateInput = (dateStr?: string | null): string => {
  const d = safeParse(dateStr);
  return d ? format(d, 'yyyy-MM-dd') : '';
};
