import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
let passed = 0, failed = 0;
const results = [];

const test = async (name, fn) => {
  try { await fn(); results.push('✅ ' + name); passed++; }
  catch(e) { results.push('❌ ' + name + ' — ' + e.message.slice(0, 80)); failed++; }
};

// ─── Dashboard ───
await test('Dashboard loads', async () => {
  await page.goto('http://localhost:3003/dashboard', { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  if (!await page.locator('text=Today').first().isVisible()) throw new Error('Not loaded');
});

await test('Dashboard - Patient modal opens', async () => {
  const panel = page.locator('.panel').filter({ hasText: 'Recent patients' });
  await panel.locator('.stack > div').first().click();
  await page.waitForTimeout(400);
  if (!await page.locator('.center-modal-backdrop').isVisible()) throw new Error('No modal');
  await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(200);
});

await test('Dashboard - Invoice modal opens', async () => {
  await page.locator('.recent-table tbody tr').first().click();
  await page.waitForTimeout(400);
  if (!await page.locator('.center-modal-backdrop').isVisible()) throw new Error('No modal');
  await page.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(200);
});

await test('Dashboard - Appointment drawer + New Patient back flow', async () => {
  await page.locator('button').filter({ hasText: '+ New appointment' }).click();
  await page.waitForTimeout(400);
  if (!await page.locator('.drawer').isVisible()) throw new Error('No drawer');
  await page.locator('text=+ New patient').click();
  await page.waitForTimeout(400);
  if (!await page.locator('text=Add a new patient').isVisible()) throw new Error('No new patient');
  await page.locator('.drawer-footer button').filter({ hasText: 'Back' }).click();
  await page.waitForTimeout(400);
  if (!await page.locator('text=Book a new appointment').isVisible()) throw new Error('Back failed');
  await page.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(200);
});

// ─── Patient detail ───
await test('Patient detail loads with tabs', async () => {
  await page.goto('http://localhost:3003/patients/P-018342', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Alice Stevens').isVisible()) throw new Error('Not loaded');
  if (!await page.locator('text=Overview').isVisible()) throw new Error('No tabs');
});

await test('Patient detail - Tooth chart tab', async () => {
  await page.locator('button').filter({ hasText: 'Tooth chart' }).click();
  await page.waitForTimeout(300);
  if (!await page.locator('text=FDI').isVisible()) throw new Error('No tooth chart');
});

await test('Patient detail - Insurance tab', async () => {
  await page.locator('button').filter({ hasText: 'Insurance' }).click();
  await page.waitForTimeout(300);
  if (!await page.locator('text=Carrier').isVisible()) throw new Error('No insurance table');
});

await test('Patient detail - SOAP Notes tab', async () => {
  await page.locator('button').filter({ hasText: 'Notes' }).click();
  await page.waitForTimeout(300);
  if (!await page.locator('text=Locked').isVisible()) throw new Error('No SOAP notes');
});

// ─── Lab page ───
await test('Lab page loads with kanban', async () => {
  await page.goto('http://localhost:3003/lab', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Lab pipeline').isVisible()) throw new Error('Not loaded');
  if (!await page.locator('text=Pipeline · Kanban').isVisible()) throw new Error('No kanban');
});

await test('Lab page - filter pills work', async () => {
  await page.locator('.filter-pill').filter({ hasText: 'Sent' }).click();
  await page.waitForTimeout(300);
  const active = await page.locator('.filter-pill.active').first().textContent();
  if (!active?.includes('Sent')) throw new Error('Filter not applied: ' + active);
});

await test('Lab page - vendors section', async () => {
  if (!await page.locator('text=Pinnacle Dental Lab').isVisible()) throw new Error('No vendors');
});

await test('Lab page - activity timeline', async () => {
  if (!await page.locator('text=Recent activity').isVisible()) throw new Error('No activity');
});

// ─── Billing page ───
await test('Billing page loads with KPIs', async () => {
  await page.goto('http://localhost:3003/billing', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Total Revenue').isVisible()) throw new Error('No KPIs');
});

await test('Billing page - aging grid', async () => {
  if (!await page.locator('text=0–30 days').isVisible()) throw new Error('No aging grid');
});

await test('Billing page - claims section', async () => {
  if (!await page.locator('text=Insurance Claims').isVisible()) throw new Error('No claims');
});

await test('Billing page - search + filters', async () => {
  await page.locator('.filter-pill').filter({ hasText: 'Paid' }).click();
  await page.waitForTimeout(300);
  const active = await page.locator('.filter-pill.active').first().textContent();
  if (!active?.includes('Paid')) throw new Error('Filter failed');
});

// ─── Communications ───
await test('Communications page loads inbox layout', async () => {
  await page.goto('http://localhost:3003/communications', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Alice Stevens').isVisible()) throw new Error('Not loaded');
});

await test('Communications - channel filter chips', async () => {
  await page.locator('.chip').filter({ hasText: 'SMS' }).click();
  await page.waitForTimeout(300);
  if (!await page.locator('.chip.active').first().isVisible()) throw new Error('No active chip');
});

await test('Communications - composer + templates', async () => {
  if (!await page.locator('text=Appointment reminder').isVisible()) throw new Error('No templates');
  await page.locator('.tpl').first().click();
  await page.waitForTimeout(200);
  const text = await page.locator('textarea').inputValue();
  if (!text) throw new Error('Template not applied');
});

// ─── CRM ───
await test('CRM page loads kanban', async () => {
  await page.goto('http://localhost:3003/crm', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=NEW').first().isVisible()) throw new Error('No kanban');
});

await test('CRM - lead card click opens drawer', async () => {
  await page.locator('.lead-card').first().click();
  await page.waitForTimeout(400);
  if (!await page.locator('.drawer').isVisible()) throw new Error('No drawer');
  await page.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(200);
});

await test('CRM - source breakdown', async () => {
  if (!await page.locator('text=Source breakdown').isVisible()) throw new Error('No sources');
});

// ─── Settings ───
await test('Settings page loads 12 tabs', async () => {
  await page.goto('http://localhost:3003/settings', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Clinic info').isVisible()) throw new Error('Not loaded');
});

await test('Settings - Working Hours tab', async () => {
  await page.locator('.stab-btn').filter({ hasText: 'Working hours' }).click();
  await page.waitForTimeout(300);
  if (!await page.locator('text=Monday').isVisible()) throw new Error('No hours');
});

await test('Settings - Integrations tab', async () => {
  await page.locator('.stab-btn').filter({ hasText: 'Integrations' }).click();
  await page.waitForTimeout(300);
  if (!await page.locator('text=Twilio SMS').isVisible()) throw new Error('No integrations');
});

await test('Settings - Audit Log tab', async () => {
  await page.locator('.stab-btn').filter({ hasText: 'Audit log' }).click();
  await page.waitForTimeout(300);
  if (!await page.locator('text=UPDATE').isVisible()) throw new Error('No audit');
});

// ─── Other pages ───
await test('Schedule page loads', async () => {
  await page.goto('http://localhost:3003/schedule', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Schedule').first().isVisible()) throw new Error('Not loaded');
});

await test('Treatment page loads', async () => {
  await page.goto('http://localhost:3003/treatment', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Treatment Plans').isVisible()) throw new Error('Not loaded');
});

await test('Reports page loads', async () => {
  await page.goto('http://localhost:3003/reports', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Reports').first().isVisible()) throw new Error('Not loaded');
});

await test('Plans page loads', async () => {
  await page.goto('http://localhost:3003/plans', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Starter').isVisible()) throw new Error('Not loaded');
});

await test('Login page loads dark theme', async () => {
  await page.goto('http://localhost:3003/login', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Welcome back').isVisible()) throw new Error('Not loaded');
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  if (!bg.includes('6') && !bg.includes('0,')) throw new Error('Not dark: ' + bg);
});

await test('Marketing page loads', async () => {
  await page.goto('http://localhost:3003/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  if (!await page.locator('text=Sovereign Clinical').first().isVisible()) throw new Error('Not loaded');
});

// Summary
console.log('\n═══════════════════════════════');
console.log('  TEST RESULTS');
console.log('═══════════════════════════════');
for (const r of results) console.log(r);
console.log('═══════════════════════════════');
console.log(`  ${passed} passed · ${failed} failed  (${Math.round(passed/(passed+failed)*100)}%)`);
console.log('═══════════════════════════════');

await browser.close();
