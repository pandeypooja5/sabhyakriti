import { describe, it, expect } from 'vitest';
import { formatINR, calcDiscountPercent, formatINRCompact } from '@/utils/currency';

describe('formatINR', () => {
  it('formats whole rupee amounts', () => {
    expect(formatINR(1250)).toContain('1,250');
    expect(formatINR(1250)).toContain('₹');
  });

  it('formats zero', () => {
    expect(formatINR(0)).toContain('0');
  });

  it('formats decimal amounts with 2 decimal places', () => {
    expect(formatINR(999.5)).toContain('999.50');
  });

  it('formats large amounts with Indian comma grouping', () => {
    const result = formatINR(100000);
    expect(result).toContain('₹');
    expect(result).toContain('1,00,000');
  });

  it('handles negative amounts', () => {
    const result = formatINR(-500);
    expect(result).toContain('500');
  });

  it('handles Infinity gracefully', () => {
    expect(formatINR(Infinity)).toBe('₹0.00');
  });

  it('handles NaN gracefully', () => {
    expect(formatINR(NaN)).toBe('₹0.00');
  });
});

describe('calcDiscountPercent', () => {
  it('calculates correct discount percentage', () => {
    expect(calcDiscountPercent(1000, 800)).toBe(20);
    expect(calcDiscountPercent(500, 375)).toBe(25);
  });

  it('returns 0 when price equals MRP', () => {
    expect(calcDiscountPercent(500, 500)).toBe(0);
  });

  it('returns 0 when MRP is 0', () => {
    expect(calcDiscountPercent(0, 0)).toBe(0);
  });

  it('returns 0 when price is greater than MRP', () => {
    expect(calcDiscountPercent(500, 600)).toBe(0);
  });
});

describe('formatINRCompact', () => {
  it('formats amounts less than 1000 without suffix', () => {
    expect(formatINRCompact(999)).toBe('₹999');
  });

  it('formats thousands as K', () => {
    expect(formatINRCompact(1500)).toBe('₹1.5K');
  });

  it('formats lakhs as L', () => {
    expect(formatINRCompact(250000)).toBe('₹2.5L');
  });
});
