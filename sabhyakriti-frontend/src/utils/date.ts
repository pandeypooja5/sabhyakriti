import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns';

const safeParse = (dateStr: string): Date => {
  const d = parseISO(dateStr);
  return isValid(d) ? d : new Date();
};

/**
 * Format date as "14 Jan 2025"
 */
export const formatDate = (dateStr: string): string => {
  return format(safeParse(dateStr), 'd MMM yyyy');
};

/**
 * Format date-time as "14 Jan 2025, 3:45 PM"
 */
export const formatDateTime = (dateStr: string): string => {
  return format(safeParse(dateStr), 'd MMM yyyy, h:mm a');
};

/**
 * Returns relative time e.g. "2 hours ago", "3 days ago"
 */
export const timeAgo = (dateStr: string): string => {
  return formatDistanceToNow(safeParse(dateStr), { addSuffix: true });
};

/**
 * Format for input[type=date] value: "2025-01-14"
 */
export const formatDateInput = (dateStr: string): string => {
  return format(safeParse(dateStr), 'yyyy-MM-dd');
};
