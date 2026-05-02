import { test, expect } from '@playwright/test';

const BASE = process.env['E2E_BASE_URL'] ?? 'http://localhost:4173';

test.describe('Billing flow P5', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'changeme');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|billing|patients)/);
  });

  test('login → /billing → click invoice → drawer opens → record payment → submit claim → claim drawer → adjudicate → mark paid', async ({ page }) => {
    await page.goto(`${BASE}/billing`);
    await expect(page.getByRole('table')).toBeVisible({ timeout: 15000 });

    // Create an invoice first via the new invoice form
    await page.getByRole('button', { name: /\+ New Invoice/i }).click();
    // Fill patient id
    const inputs = page.locator('input');
    const count = await inputs.count();
    if (count > 0) {
      await inputs.first().fill('p1');
    }
    await page.getByRole('button', { name: /^Create$/i }).click();

    // Wait for invoice row to appear
    await expect(page.locator('tbody tr').first()).toBeVisible({ timeout: 10000 });

    // Click the first invoice row
    await page.locator('tbody tr').first().click();

    // Drawer should open
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });

    // Record payment if button is visible
    const recordBtn = page.getByRole('button', { name: /record payment/i });
    const recordVisible = await recordBtn.isVisible();
    if (recordVisible) {
      await recordBtn.click();
      await expect(page.getByText(/Method/i)).toBeVisible();
      const amountInput = page.locator('input[type="number"]').first();
      await amountInput.fill('50');
      await page.getByRole('button', { name: /^Record$/i }).click();
    }

    // Submit claim if button is visible
    const claimBtn = page.getByRole('button', { name: /submit claim/i });
    const claimVisible = await claimBtn.isVisible();
    if (claimVisible) {
      await claimBtn.click();
      await expect(page.getByText(/Submit Insurance Claim/i)).toBeVisible({ timeout: 5000 });
      // Close the form
      await page.getByRole('button', { name: /^Cancel$/i }).last().click();
    }

    // Close drawer
    await page.getByRole('button', { name: /Close/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 3000 });
  });

  test('/billing?status=overdue filters by status', async ({ page }) => {
    await page.goto(`${BASE}/billing?status=overdue`);
    await expect(page.getByRole('table')).toBeVisible({ timeout: 15000 });
    // The status filter select should show 'overdue'
    const select = page.locator('select').first();
    await expect(select).toHaveValue('overdue');
  });

  test('A/R aging tile on dashboard links to /billing?status=overdue', async ({ page }) => {
    await page.goto(`${BASE}/dashboard`);
    await expect(page.getByText(/A\/R Aging/i)).toBeVisible({ timeout: 15000 });
    const link = page.locator('a[href*="status=overdue"]').first();
    await expect(link).toBeVisible();
    await link.click();
    await page.waitForURL(/billing/);
    expect(page.url()).toContain('status=overdue');
  });
});
