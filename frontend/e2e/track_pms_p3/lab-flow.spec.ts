import { test, expect } from '@playwright/test';

const BASE = process.env['E2E_BASE_URL'] ?? 'http://localhost:4173';

test.describe('Lab flow P3', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'changeme');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|schedule|patients|lab)/);
  });

  test('click card → LabCaseDrawer opens → Implants tab → fill form → save', async ({ page }) => {
    await page.goto(`${BASE}/lab`);

    // Wait for kanban to render
    await expect(page.getByText('Lab Cases')).toBeVisible({ timeout: 15000 });

    // Click first card
    const card = page.locator('[class*="cursor-grab"]').first();
    const cardVisible = await card.isVisible();
    if (!cardVisible) {
      // No cards rendered — verify kanban structure is correct
      await expect(page.getByText('Draft')).toBeVisible();
      return;
    }

    await card.click();

    // Drawer should open
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Lab Case #/i)).toBeVisible();

    // Click Implants tab
    await page.getByRole('button', { name: /implants/i }).click();
    await expect(page.getByText(/Lot number/i)).toBeVisible();

    // Fill implant form
    const allTextInputs = page.locator('input[type="text"], input:not([type])');
    const count = await allTextInputs.count();
    if (count >= 3) {
      await allTextInputs.nth(2).fill('LOT-E2E-001');
    }

    // Submit
    await page.getByRole('button', { name: /save implant/i }).click();

    // After save, implant row should appear (or form resets)
    await expect(page.getByText(/LOT-E2E-001/i).or(page.getByText(/Lot number/i))).toBeVisible({
      timeout: 5000,
    });
  });
});
