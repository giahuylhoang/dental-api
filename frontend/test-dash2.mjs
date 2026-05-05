import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto('http://localhost:3003/dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);

await page.screenshot({ path: 'test-screenshots/dash-full.png', fullPage: true });
console.log('Screenshot saved');

// Find patient cards — they're in the "Recent patients" panel, after appointments panel
const patientPanel = page.locator('.panel:has(.panel-h-title:text("Recent patients"))');
const patientCards = patientPanel.locator('.stack > div');
const count = await patientCards.count();
console.log('Patient cards found:', count);

if (count > 0) {
  await patientCards.first().click();
  await page.waitForTimeout(500);
  const modal = await page.locator('.center-modal-backdrop').isVisible();
  console.log('Patient modal visible:', modal);
  if (modal) {
    await page.screenshot({ path: 'test-screenshots/patient-modal.png' });
    await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
    await page.waitForTimeout(300);
  }
}

// Test appointment expand — click appointment card in the appointments panel
const apptPanel = page.locator('.panel:has(.panel-h-title:text("Today")');
const apptCards = apptPanel.locator('.stack > div');
const apptCount = await apptCards.count();
console.log('Appointment card wrappers:', apptCount);
if (apptCount > 0) {
  await apptCards.first().click();
  await page.waitForTimeout(500);
  const expanded = await page.locator('.appt-quick-actions').isVisible();
  console.log('Quick actions visible:', expanded);
  if (expanded) {
    await page.screenshot({ path: 'test-screenshots/appt-expanded.png' });
  }
}

console.log('Debug complete');
await browser.close();
