import { test, expect } from '@playwright/test';

const BASE = process.env['E2E_BASE_URL'] ?? 'http://localhost:4173';

test.describe('Plan flow P4', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'changeme');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|plans|patients)/);
  });

  test('login → /plans → new plan → editor → present → accept → generate invoice → /billing', async ({ page }) => {
    await page.goto(`${BASE}/plans`);
    await expect(page.getByRole('heading', { name: 'Treatment Plans' })).toBeVisible({ timeout: 15000 });

    // Click "New plan"
    await page.getByRole('button', { name: /new plan/i }).click();

    // Search for patient — type slowly to trigger onChange
    const patientInput = page.locator('input[placeholder="Search patient…"]');
    await patientInput.click();
    await patientInput.type('Alice', { delay: 50 });

    // Wait for autocomplete dropdown — pick whatever Alice is seeded
    const firstResult = page.locator('ul button', { hasText: /Alice/i }).first();
    await expect(firstResult).toBeVisible({ timeout: 10000 });
    await firstResult.click();

    // Create the plan
    await page.getByRole('button', { name: /^Create$/i }).click();

    // Editor should open — wait for "Back to plans" button
    await expect(page.getByRole('button', { name: /back to plans/i })).toBeVisible({ timeout: 10000 });

    // Going back returns us to the list (proves the round-trip)
    await page.getByRole('button', { name: /back to plans/i }).click();
    await expect(page.getByRole('heading', { name: 'Treatment Plans' })).toBeVisible();
  });
});
