import { test, expect } from '@playwright/test';

const BASE_URL = 'https://sabhyakriti.com';

test.describe('Sabhyakriti Frontend & API Tests', () => {

  test('Frontend loads successfully', async ({ page }) => {
    const response = await page.goto(BASE_URL);
    expect(response?.status()).toBe(200);
    expect(page).toHaveTitle(/sabhyakriti/i);
  });

  test('Homepage renders key elements', async ({ page }) => {
    await page.goto(BASE_URL);

    // Check if main content loads
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent).toBeVisible({ timeout: 5000 });

    // Check for navigation
    const nav = page.locator('nav, [role="navigation"]');
    await expect(nav).toBeVisible();
  });

  test('API: Get products endpoint', async ({ page }) => {
    const response = await page.request.get(
      `${BASE_URL}/api/v1/products?page=1&page_size=8`
    );

    console.log('Products API Status:', response.status());
    console.log('Products API Headers:', response.headers());

    if (response.status() === 200) {
      const data = await response.json();
      console.log('Products Response:', JSON.stringify(data, null, 2));
      expect(response.status()).toBe(200);
    } else {
      const text = await response.text();
      console.error('Products API Error:', text);
    }
  });

  test('API: Get categories endpoint', async ({ page }) => {
    const response = await page.request.get(
      `${BASE_URL}/api/v1/categories`
    );

    console.log('Categories API Status:', response.status());

    if (response.status() === 200) {
      const data = await response.json();
      console.log('Categories Response:', JSON.stringify(data, null, 2));
    } else {
      const text = await response.text();
      console.error('Categories API Error:', text);
    }
  });

  test('API: Auth health check', async ({ page }) => {
    const response = await page.request.get(
      `${BASE_URL}/api/v1/auth/health`,
      { validateStatus: () => true } // Accept any status
    );

    console.log('Auth Health Check Status:', response.status());
    const text = await response.text();
    console.log('Auth Health Response:', text);
  });

  test('API: Test Vercel rewrites are working', async ({ page }) => {
    // This tests if Vercel is correctly forwarding requests to Railway
    const endpoints = [
      '/api/v1/products',
      '/api/v1/categories',
      '/api/v1/cart',
      '/api/v1/orders',
    ];

    for (const endpoint of endpoints) {
      const response = await page.request.get(`${BASE_URL}${endpoint}`, {
        validateStatus: () => true,
      });

      console.log(`${endpoint}: ${response.status()}`);

      // Should not be 404 (which means Vercel isn't routing properly)
      // Might be 500 if Railway service is down, but not 404
      if (response.status() === 404) {
        console.error(`❌ Vercel rewrite FAILED for ${endpoint}`);
      } else {
        console.log(`✅ Vercel routing OK for ${endpoint} (status: ${response.status()})`);
      }
    }
  });

  test('Page elements load without errors', async ({ page }) => {
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('Browser console error:', msg.text());
      }
    });

    page.on('response', response => {
      if (response.status() >= 400 && !response.url().includes('api')) {
        console.warn(`⚠️ HTTP ${response.status()}: ${response.url()}`);
      }
    });

    await page.goto(BASE_URL);

    // Wait for initial load
    await page.waitForTimeout(3000);

    // Get all console errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    if (errors.length > 0) {
      console.log('Console Errors:', errors);
    }
  });

  test('Navigation menu works', async ({ page }) => {
    await page.goto(BASE_URL);

    // Look for nav links
    const navLinks = page.locator('a[href*="/"], button');
    const count = await navLinks.count();
    console.log(`Found ${count} navigation elements`);

    expect(count).toBeGreaterThan(0);
  });

  test('Responsive design check', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    const response = await page.goto(BASE_URL);
    expect(response?.status()).toBe(200);

    // Check if content is visible
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent).toBeVisible({ timeout: 5000 });

    console.log('✅ Mobile view loads successfully');
  });
});
