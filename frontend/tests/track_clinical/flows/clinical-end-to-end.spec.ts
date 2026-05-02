import { test, expect } from '@playwright/test';

test.describe('clinical end-to-end', () => {
  test('login → search patient → open 360 → navigate tabs', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/patients/);

    // Search for patient
    await page.fill('input[type="search"]', 'Alice');
    await expect(page.getByText('Alice Smith')).toBeVisible();

    // Open patient 360
    await page.getByText('Alice Smith').click();
    await expect(page.getByText('alice@example.com')).toBeVisible();

    // Navigate tabs
    await page.getByRole('button', { name: 'Denture Cases' }).click();
    await expect(page.getByText(/upper/)).toBeVisible();

    await page.getByRole('button', { name: 'Treatment Plans' }).click();
    await expect(page.getByText(/Plan #tp1/)).toBeVisible();

    await page.getByRole('button', { name: 'Appointments' }).click();
    await expect(page.getByText(/No appointments|2026-05-10/)).toBeVisible();
  });
});
