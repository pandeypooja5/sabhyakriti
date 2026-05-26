/**
 * Format a number as Indian Rupees.
 * e.g. formatINR(1250) → "₹1,250.00"
 */
export const formatINR = (amount: number): string => {
  if (!isFinite(amount)) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format compact amount for display e.g. "₹1.2K" or "₹4.5L"
 */
export const formatINRCompact = (amount: number): string => {
  if (!isFinite(amount)) return '₹0';
  if (amount >= 100_000) return `₹${(amount / 100_000).toFixed(1)}L`;
  if (amount >= 1_000) return `₹${(amount / 1_000).toFixed(1)}K`;
  return `₹${amount.toFixed(0)}`;
};

/**
 * Calculate discount percentage between MRP and selling price.
 */
export const calcDiscountPercent = (mrp: number, price: number): number => {
  if (mrp <= 0 || price >= mrp) return 0;
  return Math.round(((mrp - price) / mrp) * 100);
};
