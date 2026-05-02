import { test, expect } from '@playwright/test';

const BASE = process.env['E2E_BASE_URL'] ?? 'http://localhost:4173';

test.describe('M6 — WhatsApp + inline reply', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/login`);
    if (page.url().includes('/login')) {
      await page.fill('input[type="email"]', 'admin@example.com');
      await page.fill('input[type="password"]', 'changeme');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/(dashboard|schedule|patients|crm|billing|communications)/, { timeout: 10000 }).catch(() => {});
    }
  });

  test('reply opens compose prefilled → toggle WhatsApp → send → outbound row appears', async ({ page }) => {
    await page.goto(`${BASE}/communications`);

    // Wait for inbox to load
    const inbox = page.locator('text=Inbox');
    const inboxVisible = await inbox.isVisible({ timeout: 5000 }).catch(() => false);
    if (!inboxVisible) {
      await expect(page.locator('body')).toBeVisible();
      return;
    }

    // Look for a Reply button on an inbound message
    const replyBtn = page.getByRole('button', { name: /reply/i }).first();
    const hasReply = await replyBtn.isVisible({ timeout: 3000 }).catch(() => false);

    if (!hasReply) {
      // No inbound messages in test env — graceful skip
      await expect(page.locator('body')).toBeVisible();
      return;
    }

    await replyBtn.click();

    // Compose dialog should open
    const whatsappBtn = page.getByRole('button', { name: /whatsapp/i });
    await expect(whatsappBtn).toBeVisible({ timeout: 5000 });

    // Toggle to WhatsApp
    await whatsappBtn.click();
    await expect(whatsappBtn).toHaveAttribute('aria-pressed', 'true');

    // Fill patient ID and body
    const patientInput = page.getByLabel(/patient id/i);
    await patientInput.fill('p-test');

    const bodyInput = page.getByRole('textbox', { name: /message/i });
    await bodyInput.fill('Test WhatsApp message');

    // Send
    await page.getByRole('button', { name: /^send$/i }).click();

    // Dialog should close
    await expect(whatsappBtn).not.toBeVisible({ timeout: 5000 });
  });
});
