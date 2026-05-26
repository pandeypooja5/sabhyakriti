# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\e2e.spec.ts >> Sabhyakriti Frontend & API Tests >> Frontend loads successfully
- Location: tests\e2e.spec.ts:7:3

# Error details

```
Error: expect(page).toHaveTitle(expected) failed

Expected pattern: /sabhyakriti/i
Received string:  ""

Call log:
  - Expect "toHaveTitle" with timeout 5000ms

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | const BASE_URL = 'https://sabhyakriti.com';
  4   | 
  5   | test.describe('Sabhyakriti Frontend & API Tests', () => {
  6   | 
  7   |   test('Frontend loads successfully', async ({ page }) => {
  8   |     const response = await page.goto(BASE_URL);
  9   |     expect(response?.status()).toBe(200);
> 10  |     expect(page).toHaveTitle(/sabhyakriti/i);
      |                  ^ Error: expect(page).toHaveTitle(expected) failed
  11  |   });
  12  | 
  13  |   test('Homepage renders key elements', async ({ page }) => {
  14  |     await page.goto(BASE_URL);
  15  | 
  16  |     // Check if main content loads
  17  |     const mainContent = page.locator('main, [role="main"]');
  18  |     await expect(mainContent).toBeVisible({ timeout: 5000 });
  19  | 
  20  |     // Check for navigation
  21  |     const nav = page.locator('nav, [role="navigation"]');
  22  |     await expect(nav).toBeVisible();
  23  |   });
  24  | 
  25  |   test('API: Get products endpoint', async ({ page }) => {
  26  |     const response = await page.request.get(
  27  |       `${BASE_URL}/api/v1/products?page=1&page_size=8`
  28  |     );
  29  | 
  30  |     console.log('Products API Status:', response.status());
  31  |     console.log('Products API Headers:', response.headers());
  32  | 
  33  |     if (response.status() === 200) {
  34  |       const data = await response.json();
  35  |       console.log('Products Response:', JSON.stringify(data, null, 2));
  36  |       expect(response.status()).toBe(200);
  37  |     } else {
  38  |       const text = await response.text();
  39  |       console.error('Products API Error:', text);
  40  |     }
  41  |   });
  42  | 
  43  |   test('API: Get categories endpoint', async ({ page }) => {
  44  |     const response = await page.request.get(
  45  |       `${BASE_URL}/api/v1/categories`
  46  |     );
  47  | 
  48  |     console.log('Categories API Status:', response.status());
  49  | 
  50  |     if (response.status() === 200) {
  51  |       const data = await response.json();
  52  |       console.log('Categories Response:', JSON.stringify(data, null, 2));
  53  |     } else {
  54  |       const text = await response.text();
  55  |       console.error('Categories API Error:', text);
  56  |     }
  57  |   });
  58  | 
  59  |   test('API: Auth health check', async ({ page }) => {
  60  |     const response = await page.request.get(
  61  |       `${BASE_URL}/api/v1/auth/health`,
  62  |       { validateStatus: () => true } // Accept any status
  63  |     );
  64  | 
  65  |     console.log('Auth Health Check Status:', response.status());
  66  |     const text = await response.text();
  67  |     console.log('Auth Health Response:', text);
  68  |   });
  69  | 
  70  |   test('API: Test Vercel rewrites are working', async ({ page }) => {
  71  |     // This tests if Vercel is correctly forwarding requests to Railway
  72  |     const endpoints = [
  73  |       '/api/v1/products',
  74  |       '/api/v1/categories',
  75  |       '/api/v1/cart',
  76  |       '/api/v1/orders',
  77  |     ];
  78  | 
  79  |     for (const endpoint of endpoints) {
  80  |       const response = await page.request.get(`${BASE_URL}${endpoint}`, {
  81  |         validateStatus: () => true,
  82  |       });
  83  | 
  84  |       console.log(`${endpoint}: ${response.status()}`);
  85  | 
  86  |       // Should not be 404 (which means Vercel isn't routing properly)
  87  |       // Might be 500 if Railway service is down, but not 404
  88  |       if (response.status() === 404) {
  89  |         console.error(`❌ Vercel rewrite FAILED for ${endpoint}`);
  90  |       } else {
  91  |         console.log(`✅ Vercel routing OK for ${endpoint} (status: ${response.status()})`);
  92  |       }
  93  |     }
  94  |   });
  95  | 
  96  |   test('Page elements load without errors', async ({ page }) => {
  97  |     page.on('console', msg => {
  98  |       if (msg.type() === 'error') {
  99  |         console.error('Browser console error:', msg.text());
  100 |       }
  101 |     });
  102 | 
  103 |     page.on('response', response => {
  104 |       if (response.status() >= 400 && !response.url().includes('api')) {
  105 |         console.warn(`⚠️ HTTP ${response.status()}: ${response.url()}`);
  106 |       }
  107 |     });
  108 | 
  109 |     await page.goto(BASE_URL);
  110 | 
```