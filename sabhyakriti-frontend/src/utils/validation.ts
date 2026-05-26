/**
 * Validate Indian mobile number (10 digits, starts with 6-9).
 */
export const isValidIndianPhone = (phone: string): boolean => {
  const cleaned = phone.replace(/\D/g, '');
  return /^[6-9]\d{9}$/.test(cleaned);
};

/**
 * Validate Indian PIN code (6 digits, first digit not 0).
 */
export const isValidPincode = (pincode: string): boolean => {
  return /^[1-9]\d{5}$/.test(pincode.trim());
};

/**
 * Validate email address.
 */
export const isValidEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
};

/**
 * Validate password strength: min 8 chars, 1 uppercase, 1 lowercase, 1 digit.
 */
export const isStrongPassword = (password: string): boolean => {
  return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(password);
};

/**
 * Validate OTP: exactly 6 digits.
 */
export const isValidOTP = (otp: string): boolean => {
  return /^\d{6}$/.test(otp.trim());
};
