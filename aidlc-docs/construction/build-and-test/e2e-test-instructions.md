# End-to-End Test Instructions — Sabhyakriti Platform

E2E tests simulate real user journeys in a browser against all running services.
**Tool: Playwright (TypeScript)**

---

## Setup

```bash
cd sabhyakriti-frontend
npm install @playwright/test
npx playwright install chromium firefox
```

Create `playwright.config.ts`:
```typescript
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  baseURL: 'http://localhost:5173',
  use: { headless: true, screenshot: 'only-on-failure', video: 'retain-on-failure' },
  timeout: 30000,
});
```

Start all services before running:
```bash
docker-compose -f docker-compose.all.yml up -d
npm run dev &
```

---

## E2E Flow 1: Homepage → Browse → PDP

```typescript
// e2e/browse.spec.ts
import { test, expect } from '@playwright/test';

test('Homepage loads with hero and categories', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('hero-banner')).toBeVisible();
  await expect(page.getByTestId('category-shortcuts')).toBeVisible();
  await expect(page.getByTestId('featured-products')).toBeVisible();
});

test('PLP: filter by Fabric=Silk', async ({ page }) => {
  await page.goto('/sarees');
  await page.getByTestId('filter-fabric-silk').click();
  await expect(page.getByTestId('product-grid')).toBeVisible();
  await expect(page.getByTestId('product-count')).toContainText(/\d+ products/);
});

test('PLP to PDP navigation', async ({ page }) => {
  await page.goto('/sarees');
  await page.getByTestId('product-card').first().click();
  await expect(page).toHaveURL(/\/sarees\//);
  await expect(page.getByTestId('pdp-image-gallery')).toBeVisible();
  await expect(page.getByTestId('add-to-cart-btn')).toBeVisible();
});

test('PDP image zoom on click', async ({ page }) => {
  await page.goto('/sarees/kanjivaram-silk-red');
  await page.getByTestId('pdp-main-image').click();
  await expect(page.getByTestId('image-lightbox')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByTestId('image-lightbox')).not.toBeVisible();
});
```

---

## E2E Flow 2: Registration → Login → Cart → Checkout

```typescript
// e2e/checkout.spec.ts
import { test, expect } from '@playwright/test';

const testUser = { email: `e2e_${Date.now()}@test.com`, password: 'E2ETest1!' };

test('Full registration and email verification flow', async ({ page }) => {
  await page.goto('/register');
  await page.getByTestId('register-email-input').fill(testUser.email);
  await page.getByTestId('register-password-input').fill(testUser.password);
  await page.getByTestId('register-fullname-input').fill('E2E Tester');
  await page.getByTestId('register-submit-btn').click();
  await expect(page.getByText('verify your email')).toBeVisible();
});

test('Add to cart and proceed to checkout', async ({ page, request }) => {
  // Login via API for speed
  const loginResp = await request.post('http://localhost:8001/api/v1/auth/login',
    { data: { email: 'verified@test.com', password: 'TestPass1!' } });
  const { tokens } = await loginResp.json();

  await page.goto('/sarees');
  await page.getByTestId('product-card').first().click();
  await page.getByTestId('add-to-cart-btn').click();
  await expect(page.getByTestId('cart-count-badge')).toContainText('1');

  await page.goto('/cart');
  await expect(page.getByTestId('cart-item')).toHaveCount(1);
  await expect(page.getByTestId('cart-gst-amount')).toBeVisible();
  await page.getByTestId('checkout-btn').click();
  await expect(page).toHaveURL('/checkout');
});

test('Checkout: select address, choose COD, place order', async ({ page }) => {
  await page.goto('/checkout');
  // Address step
  await page.getByTestId('address-option').first().click();
  await page.getByTestId('continue-to-payment-btn').click();
  // Payment step
  await page.getByTestId('payment-cod-option').click();
  await page.getByTestId('continue-to-review-btn').click();
  // Review step
  await expect(page.getByTestId('order-review-total')).toBeVisible();
  await page.getByTestId('place-order-btn').click();
  // Confirmation
  await expect(page).toHaveURL(/\/order-confirmation\//);
  await expect(page.getByTestId('order-number')).toContainText('SKB-');
});
```

---

## E2E Flow 3: Order Management

```typescript
// e2e/orders.spec.ts
test('View order history and detail', async ({ page }) => {
  await page.goto('/orders');
  await expect(page.getByTestId('order-history-list')).toBeVisible();
  await page.getByTestId('order-row').first().click();
  await expect(page.getByTestId('order-status-timeline')).toBeVisible();
  await expect(page.getByTestId('invoice-download-btn')).toBeVisible();
});
```

---

## E2E Flow 4: Admin Panel

```typescript
// e2e/admin.spec.ts
test('Admin dashboard loads KPIs', async ({ page }) => {
  // Login as admin (pre-created in seed data)
  await page.goto('/login');
  await page.getByTestId('login-email-input').fill('admin@sabhyakriti.com');
  await page.getByTestId('login-password-input').fill('AdminPass1!');
  await page.getByTestId('login-submit-btn').click();
  // MFA step for admin
  await page.getByTestId('totp-input').fill('000000'); // use test TOTP secret
  await page.getByTestId('mfa-verify-btn').click();

  await page.goto('/admin');
  await expect(page.getByTestId('kpi-revenue-30d')).toBeVisible();
  await expect(page.getByTestId('kpi-orders-30d')).toBeVisible();
  await expect(page.getByTestId('kpi-pending-orders')).toBeVisible();
});
```

---

## Run All E2E Tests

```bash
cd sabhyakriti-frontend
npx playwright test e2e/              # headless
npx playwright test e2e/ --headed     # visible browser (debugging)
npx playwright show-report            # open HTML report after run
```

Expected: all critical user flows pass before production deployment.
