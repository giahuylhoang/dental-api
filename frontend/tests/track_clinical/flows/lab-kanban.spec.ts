import { test, expect } from '@playwright/test';

test.describe('lab kanban', () => {
  test('renders kanban columns', async ({ page }) => {
    // Set auth state so we can access the lab page
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/patients/);

    await page.goto('/lab');
    await expect(page.getByText('Lab Cases')).toBeVisible();
    await expect(page.getByText('Sent')).toBeVisible();
    await expect(page.getByText('In Progress')).toBeVisible();
    await expect(page.getByText('Returned')).toBeVisible();
  });
});
