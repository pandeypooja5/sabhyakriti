import { describe, it, expect } from 'vitest';
import { isValidIndianPhone, isValidPincode, isValidEmail, isStrongPassword } from '@/utils/validation';

describe('isValidIndianPhone', () => {
  it('accepts valid 10-digit numbers starting with 6-9', () => {
    expect(isValidIndianPhone('9876543210')).toBe(true);
    expect(isValidIndianPhone('8123456789')).toBe(true);
    expect(isValidIndianPhone('7000000000')).toBe(true);
    expect(isValidIndianPhone('6543210987')).toBe(true);
  });

  it('rejects numbers starting with 0-5', () => {
    expect(isValidIndianPhone('5876543210')).toBe(false);
    expect(isValidIndianPhone('4123456789')).toBe(false);
    expect(isValidIndianPhone('0000000000')).toBe(false);
  });

  it('rejects numbers with wrong length', () => {
    expect(isValidIndianPhone('987654321')).toBe(false); // 9 digits
    expect(isValidIndianPhone('98765432100')).toBe(false); // 11 digits
  });

  it('handles numbers with country code', () => {
    expect(isValidIndianPhone('+919876543210')).toBe(true); // stripped to 10 digits
  });

  it('rejects empty string', () => {
    expect(isValidIndianPhone('')).toBe(false);
  });
});

describe('isValidPincode', () => {
  it('accepts valid 6-digit pincodes not starting with 0', () => {
    expect(isValidPincode('110001')).toBe(true);
    expect(isValidPincode('400001')).toBe(true);
    expect(isValidPincode('560001')).toBe(true);
  });

  it('rejects pincodes starting with 0', () => {
    expect(isValidPincode('010001')).toBe(false);
  });

  it('rejects pincodes with wrong length', () => {
    expect(isValidPincode('11000')).toBe(false); // 5 digits
    expect(isValidPincode('1100011')).toBe(false); // 7 digits
  });

  it('rejects non-numeric pincodes', () => {
    expect(isValidPincode('1100A1')).toBe(false);
  });
});

describe('isValidEmail', () => {
  it('accepts valid email addresses', () => {
    expect(isValidEmail('user@example.com')).toBe(true);
    expect(isValidEmail('user.name+tag@domain.co.in')).toBe(true);
    expect(isValidEmail('user@subdomain.example.org')).toBe(true);
  });

  it('rejects invalid email addresses', () => {
    expect(isValidEmail('not-an-email')).toBe(false);
    expect(isValidEmail('@example.com')).toBe(false);
    expect(isValidEmail('user@')).toBe(false);
    expect(isValidEmail('')).toBe(false);
  });
});

describe('isStrongPassword', () => {
  it('accepts passwords with all requirements', () => {
    expect(isStrongPassword('Password1')).toBe(true);
    expect(isStrongPassword('SecurePass123')).toBe(true);
  });

  it('rejects passwords shorter than 8 chars', () => {
    expect(isStrongPassword('Pass1')).toBe(false);
  });

  it('rejects passwords without uppercase', () => {
    expect(isStrongPassword('password1')).toBe(false);
  });

  it('rejects passwords without lowercase', () => {
    expect(isStrongPassword('PASSWORD1')).toBe(false);
  });

  it('rejects passwords without digits', () => {
    expect(isStrongPassword('Password')).toBe(false);
  });
});
