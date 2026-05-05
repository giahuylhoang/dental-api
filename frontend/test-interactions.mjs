import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
let p = 0, f = 0;
const T = async (label, fn) => { try { await fn(page); console.log('✅ ' + label); p++; } catch(e) { console.log('❌ ' + label + ' — ' + e.message.slice(0, 90)); f++; }};
const nav = async url => { await page.goto(url, { waitUntil: 'networkidle' }); await page.waitForTimeout(600); };

// 1. Patients: +New patient → drawer
await nav('http://localhost:3003/patients');
await T('Patients: +New patient opens drawer', async p => {
  await p.locator('button').filter({ hasText: '+ New patient' }).click();
  await p.waitForTimeout(400);
  if (!await p.locator('.drawer').isVisible()) throw new Error('No drawer');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
  await p.waitForTimeout(200);
});

// 2. Schedule: +New appointment → drawer
await nav('http://localhost:3003/schedule');
await T('Schedule: +New appointment opens drawer', async p => {
  await p.locator('button').filter({ hasText: '+ New appointment' }).click();
  await p.waitForTimeout(400);
  if (!await p.locator('.drawer').isVisible()) throw new Error('No drawer');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
});

// 3. Treatment: +New plan → drawer
await nav('http://localhost:3003/treatment');
await T('Treatment: +New plan opens drawer', async p => {
  await p.locator('button').filter({ hasText: '+ New plan' }).click();
  await p.waitForTimeout(400);
  if (!await p.locator('.drawer').isVisible()) throw new Error('No drawer');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
});

// 4. Treatment: click plan → modal
await T('Treatment: Click plan row opens modal', async p => {
  await p.locator('table.list tbody tr').first().click();
  await p.waitForTimeout(400);
  if (!await p.locator('.center-modal-backdrop').isVisible()) throw new Error('No modal');
  await p.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
});

// 5. Lab: +New case → drawer
await nav('http://localhost:3003/lab');
await T('Lab: +New lab case opens drawer', async p => {
  await p.locator('button').filter({ hasText: '+ New lab case' }).click();
  await p.waitForTimeout(400);
  if (!await p.locator('.drawer').isVisible()) throw new Error('No drawer');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
});

// 6. Lab: click case row → modal
await T('Lab: Click case row opens modal', async p => {
  await p.locator('table.cases tbody tr').first().click();
  await p.waitForTimeout(400);
  if (!await p.locator('.center-modal-backdrop').isVisible()) throw new Error('No modal');
  await p.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
});

// 7. Billing: +New invoice → drawer
await nav('http://localhost:3003/billing');
await T('Billing: +New invoice opens drawer', async p => {
  await p.locator('button').filter({ hasText: '+ New invoice' }).click();
  await p.waitForTimeout(400);
  if (!await p.locator('.drawer').isVisible()) throw new Error('No drawer');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
});

// 8. Patient detail: Schedule → drawer
await nav('http://localhost:3003/patients/P-018342');
await T('Patient detail: Schedule opens drawer', async p => {
  await p.locator('button').filter({ hasText: 'Schedule' }).first().click();
  await p.waitForTimeout(400);
  if (!await p.locator('.drawer').isVisible()) throw new Error('No drawer');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
});

// 9. CRM: +New lead → drawer
await nav('http://localhost:3003/crm');
await T('CRM: +New lead opens drawer', async p => {
  await p.locator('button').filter({ hasText: '+ New lead' }).click();
  await p.waitForTimeout(400);
  if (!await p.locator('.drawer').isVisible()) throw new Error('No drawer');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
});

// 10. Dashboard: all working
await nav('http://localhost:3003/dashboard');
await T('Dashboard: Patient modal', async p => {
  const panel = p.locator('.panel').filter({ hasText: 'Recent patients' });
  await panel.locator('.stack > div').first().click();
  await p.waitForTimeout(400);
  if (!await p.locator('.center-modal-backdrop').isVisible()) throw new Error('No modal');
  await p.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
});

await T('Dashboard: Invoice modal', async p => {
  await p.locator('.recent-table tbody tr').first().click();
  await p.waitForTimeout(400);
  if (!await p.locator('.center-modal-backdrop').isVisible()) throw new Error('No modal');
  await p.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
});

await T('Dashboard: Appointment drawer + New Patient back', async p => {
  await p.locator('button').filter({ hasText: '+ New appointment' }).click();
  await p.waitForTimeout(400);
  await p.locator('text=+ New patient').click();
  await p.waitForTimeout(400);
  if (!await p.locator('text=Add a new patient').isVisible()) throw new Error('No new patient');
  await p.locator('.drawer-footer button').filter({ hasText: 'Back' }).click();
  await p.waitForTimeout(400);
  if (!await p.locator('text=Book a new appointment').isVisible()) throw new Error('Back failed');
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
});

console.log(`\n=== Results: ${p} passed · ${f} failed ===`);
await browser.close();
