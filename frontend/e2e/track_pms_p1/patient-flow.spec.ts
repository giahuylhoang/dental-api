import { test, expect } from '@playwright/test';

const BASE = process.env['E2E_BASE_URL'] ?? 'http://localhost:4173';

test.describe('Patient360 P1 flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'changeme');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|patients)/);
  });

  test('quick-books a new patient and fills P1 tabs', async ({ page }) => {
    await page.goto(`${BASE}/patients`);
    await expect(page.getByRole('heading', { name: 'Patients' })).toBeVisible();

    const firstLink = page.locator('table tbody tr:first-child a').first();
    await firstLink.click();
    await page.waitForURL(/\/patients\/.+/);

    // --- Medical tab ---
    await page.getByRole('button', { name: 'Medical', exact: true }).click();
    await expect(page).toHaveURL(/tab=medical/);
    await page.locator('textarea#medical_history').fill('No known conditions');
    await page.getByRole('button', { name: /^Save$/ }).click();

    // --- Documents tab ---
    await page.getByRole('button', { name: 'Documents', exact: true }).click();
    await expect(page).toHaveURL(/tab=documents/);
    await page.locator('input[type="file"]').setInputFiles({
      name: 'test.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('fake-image-data'),
    });
    await page.getByRole('button', { name: /^Upload$/ }).click();

    // --- Insurance tab ---
    await page.getByRole('button', { name: 'Insurance', exact: true }).click();
    await expect(page).toHaveURL(/tab=insurance/);
    await page.getByRole('button', { name: /Add insurance/ }).click();
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await page.fill('input#carrier', 'Blue Cross');
    await page.fill('input#policy_number', 'BC-12345');
    await page.fill('input#holder_name', 'Alice Smith');
    // Submit the drawer form via its form attribute (unique button)
    await page.locator('button[form="insurance-form"][type="submit"]').click();
    await expect(page.locator('text=Blue Cross').first()).toBeVisible({ timeout: 10000 });

    // --- Status tab ---
    await page.getByRole('button', { name: 'Status', exact: true }).click();
    await expect(page).toHaveURL(/tab=status/);
    await expect(page.getByText(/Current status:/)).toBeVisible();
  });
});
