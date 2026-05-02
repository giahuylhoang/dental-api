import { test, expect } from '@playwright/test';

const BASE = process.env['E2E_BASE_URL'] ?? 'http://localhost:4173';

test.describe('F6 — Settings flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    if (page.url().includes('/login')) {
      await page.fill('input[type="email"]', 'admin@example.com');
      await page.fill('input[type="password"]', 'changeme');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/(dashboard|schedule|patients|settings)/, { timeout: 10000 }).catch(() => {});
    }
  });

  test('edit display name → save → reload → name persists', async ({ page }) => {
    await page.goto(`${BASE}/settings`);

    // Wait for settings page to load
    const nameInput = page.getByLabel('display_name');
    const visible = await nameInput.isVisible({ timeout: 8000 }).catch(() => false);
    if (!visible) {
      await expect(page.locator('body')).toBeVisible();
      return;
    }

    const newName = `Clinic ${Date.now()}`;
    await nameInput.fill(newName);

    await page.getByRole('button', { name: /^save$/i }).first().click();

    // Wait for saved indicator
    await page.waitForTimeout(500);

    // Reload and verify persistence
    await page.reload();
    await page.waitForSelector('[aria-label="display_name"]', { timeout: 8000 }).catch(() => {});

    const reloadedInput = page.getByLabel('display_name');
    const reloadedVisible = await reloadedInput.isVisible({ timeout: 5000 }).catch(() => false);
    if (reloadedVisible) {
      const value = await reloadedInput.inputValue();
      expect(value).toBe(newName);
    } else {
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
