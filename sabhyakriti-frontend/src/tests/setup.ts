import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock react-medium-image-zoom
vi.mock('react-medium-image-zoom', () => ({
  default: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
  },
  Toaster: () => null,
}));

// Mock Razorpay
Object.defineProperty(window, 'Razorpay', {
  value: vi.fn(() => ({
    open: vi.fn(),
    on: vi.fn(),
  })),
  writable: true,
});
