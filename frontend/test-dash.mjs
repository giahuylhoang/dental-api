import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto('http://localhost:3003/dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);

// Test 1: Patient modal
const patientCards = page.locator('.stack > div').first();
await patientCards.click();
await page.waitForTimeout(500);
let modal = await page.locator('.center-modal-backdrop').isVisible();
console.log(modal ? 'PASS 1/7 Patient modal opens' : 'FAIL 1/7 Patient modal');
if (modal) {
  const btn = await page.locator('.btn-primary:has-text("Open chart")').isVisible();
  console.log(btn ? 'PASS 2/7 Open chart button present' : 'FAIL 2/7');
  await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(300);
}

// Test 2: Invoice modal
const invRow = page.locator('.recent-table tbody tr').first();
await invRow.click();
await page.waitForTimeout(500);
modal = await page.locator('.center-modal-backdrop').isVisible();
console.log(modal ? 'PASS 3/7 Invoice modal opens' : 'FAIL 3/7 Invoice modal');
if (modal) {
  await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(300);
}

// Test 3: Appointment drawer
await page.locator('button:has-text("+ New appointment")').click();
await page.waitForTimeout(500);
let drawer = await page.locator('.drawer').isVisible();
console.log(drawer ? 'PASS 4/7 Appointment drawer opens' : 'FAIL 4/7 Drawer');
if (drawer) {
  // Test 4: New Patient nested flow
  const newPt = page.locator('.field-link:has-text("+ New patient")');
  if (await newPt.isVisible()) {
    await newPt.click();
    await page.waitForTimeout(500);
    const title = await page.locator('.drawer-title:has-text("Add a new patient")').isVisible();
    console.log(title ? 'PASS 5/7 New Patient nested' : 'FAIL 5/7');
    const back = page.locator('.drawer-footer button:has-text("Back")');
    if (await back.isVisible()) {
      await back.click();
      await page.waitForTimeout(500);
      const apptTitle = await page.locator('.drawer-title:has-text("Book a new appointment")').isVisible();
      console.log(apptTitle ? 'PASS 6/7 Back returns to appointment' : 'FAIL 6/7');
    }
  }
  await page.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(300);
}

// Test 5: Appointment expand + workspace
const apptCard = page.locator('.stack > div').first();
await apptCard.click();
await page.waitForTimeout(300);
const expanded = await page.locator('.appt-quick-actions').isVisible();
console.log(expanded ? 'PASS 7/7 Appointment expands' : 'FAIL 7/7');
if (expanded) {
  const openWs = page.locator('.appt-quick-actions .btn-primary:has-text("Open Chart")');
  if (await openWs.isVisible()) {
    await openWs.click();
    await page.waitForTimeout(500);
    const wsModal = await page.locator('.center-modal-backdrop').isVisible();
    console.log(wsModal ? 'PASS Bonus: Workspace modal' : 'INFO: Workspace check');
    if (wsModal) {
      await page.locator('.appt-ws-actions .btn-primary:has-text("Confirm")').click();
      await page.waitForTimeout(300);
    }
  }
}

console.log('\n=== All Dashboard Tests Complete ===');
await browser.close();
