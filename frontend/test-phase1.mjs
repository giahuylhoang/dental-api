import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:3003/dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);

let passed = 0, failed = 0;
const test = async (name, fn) => {
  try { await fn(); console.log('✅ ' + name); passed++; }
  catch(e) { console.log('❌ ' + name + ' — ' + e.message.split('\n')[0]); failed++; }
};

// 1. Patient modal
await test('Patient card click opens overview modal', async () => {
  const panel = page.locator('.panel').filter({ hasText: 'Recent patients' });
  await panel.locator('.stack > div').first().click();
  await page.waitForTimeout(500);
  if (!await page.locator('.center-modal-backdrop').isVisible()) throw new Error('Modal not visible');
  if (!await page.locator('text=Open chart').isVisible()) throw new Error('Open chart button missing');
  await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(300);
});

// 2. Invoice modal  
await test('Invoice row click opens overview modal', async () => {
  await page.locator('.recent-table tbody tr').first().click();
  await page.waitForTimeout(500);
  if (!await page.locator('.center-modal-backdrop').isVisible()) throw new Error('Modal not visible');
  if (!await page.locator('text=View invoice').isVisible()) throw new Error('View invoice missing');
  await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(300);
});

// 3. Appointment drawer
await test('+ New appointment opens booking drawer', async () => {
  await page.locator('button').filter({ hasText: '+ New appointment' }).click();
  await page.waitForTimeout(500);
  if (!await page.locator('.drawer').isVisible()) throw new Error('Drawer not visible');
});

// 4. New Patient nested
await test('+ New patient from appointment → back returns to appointment', async () => {
  await page.locator('text=+ New patient').click();
  await page.waitForTimeout(500);
  if (!await page.locator('text=Add a new patient').isVisible()) throw new Error('New patient not shown');
  await page.locator('.drawer-footer button').filter({ hasText: 'Back' }).click();
  await page.waitForTimeout(500);
  if (!await page.locator('text=Book a new appointment').isVisible()) throw new Error('Did not return');
  await page.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(300);
});

// 5. Appointment expand + workspace
await test('Appointment expands + Open Chart shows workspace', async () => {
  const panel = page.locator('.panel').filter({ hasText: "Today's appointments" });
  await panel.locator('.stack > div').first().click();
  await page.waitForTimeout(500);
  if (!await page.locator('.appt-quick-actions').isVisible()) throw new Error('Quick actions not shown');
  await page.locator('.appt-quick-actions button').filter({ hasText: 'Open Chart' }).click();
  await page.waitForTimeout(500);
  if (!await page.locator('.center-modal-backdrop').isVisible()) throw new Error('Workspace modal not visible');
  if (!await page.locator('text=Confirm').isVisible()) throw new Error('Confirm button missing');
  await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(300);
});

console.log(`\n=== Phase 1 Results: ${passed} passed, ${failed} failed ===`);
await browser.close();
