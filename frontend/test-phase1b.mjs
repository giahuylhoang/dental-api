import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:3003/dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);

// Appointment expand + workspace
const panel = page.locator('.panel').filter({ hasText: "Today's appointments" });
await panel.locator('.stack > div').first().click();
await page.waitForTimeout(500);
const expanded = await page.locator('.appt-quick-actions').isVisible();
console.log('Expanded:', expanded);

if (expanded) {
  await page.locator('.appt-quick-actions button').filter({ hasText: 'Open Chart' }).click();
  await page.waitForTimeout(500);
  const wsVisible = await page.locator('.center-modal-backdrop').isVisible();
  console.log('Workspace modal:', wsVisible);
  
  if (wsVisible) {
    const confirmBtns = await page.locator('.appt-ws-actions .btn-primary').count();
    console.log('Action buttons with btn-primary:', confirmBtns);
    
    // Click Confirm specifically
    await page.locator('.appt-ws-actions .btn-primary').first().click();
    await page.waitForTimeout(500);
    console.log('Clicked Confirm');
  }
}

console.log('Done');
await browser.close();
