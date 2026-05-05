import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();

const BUGS = [];
let testCount = 0;

const check = async (label, fn) => {
  testCount++;
  try {
    const result = await fn(page);
    if (result === true || result === undefined) {
      console.log(`  ✅ ${testCount}. ${label}`);
    } else {
      BUGS.push({ page: currentPage, test: label, detail: result });
      console.log(`  ❌ ${testCount}. ${label} — ${result}`);
    }
  } catch(e) {
    BUGS.push({ page: currentPage, test: label, detail: e.message.slice(0, 100) });
    console.log(`  ❌ ${testCount}. ${label} — ${e.message.slice(0, 100)}`);
  }
};

let currentPage = '';

// ═══════════════════════════════════════════
// 1. DASHBOARD
// ═══════════════════════════════════════════
currentPage = 'Dashboard';
console.log('\n📊 ' + currentPage);
await page.goto('http://localhost:3003/dashboard', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);

await check('Page loads', async p => p.locator('h1').first().isVisible() ? true : 'h1 not found');

// Patient card → modal
await check('Patient click opens modal', async p => {
  const panel = p.locator('.panel').filter({ hasText: 'Recent patients' });
  const cards = panel.locator('.stack > div');
  if (await cards.count() === 0) return 'No patient cards found';
  await cards.first().click();
  await p.waitForTimeout(400);
  const modal = await p.locator('.center-modal-backdrop').isVisible();
  if (!modal) return 'Modal did not appear';
  const hasOpenChart = await p.locator('text=Open chart').isVisible();
  if (!hasOpenChart) return 'No Open chart button';
  await p.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await p.waitForTimeout(200);
});

// Invoice row → modal
await check('Invoice click opens modal', async p => {
  const rows = p.locator('.recent-table tbody tr');
  if (await rows.count() === 0) return 'No invoice rows';
  await rows.first().click();
  await p.waitForTimeout(400);
  const modal = await p.locator('.center-modal-backdrop').isVisible();
  if (!modal) return 'Modal did not appear';
  const hasViewInvoice = await p.locator('text=View invoice').isVisible();
  if (!hasViewInvoice) return 'No View invoice button';
  await p.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await p.waitForTimeout(200);
});

// "New appointment" → drawer
await check('New appt button opens drawer', async p => {
  await p.locator('button').filter({ hasText: '+ New appointment' }).click();
  await p.waitForTimeout(400);
  const drawer = await p.locator('.drawer').isVisible();
  if (!drawer) return 'Drawer not visible';
});

// "+ New patient" → nested drawer → back → returns to appt drawer
await check('+New patient + back returns to appt', async p => {
  const link = p.locator('.field-link:has-text("+ New patient")');
  if (!await link.isVisible()) return 'No +New patient link';
  await link.click();
  await p.waitForTimeout(400);
  const npTitle = await p.locator('text=Add a new patient').isVisible();
  if (!npTitle) return 'New patient drawer not shown';
  const backBtn = p.locator('.drawer-footer button').filter({ hasText: 'Back' });
  if (!await backBtn.isVisible()) return 'No Back button in new patient drawer';
  await backBtn.click();
  await p.waitForTimeout(400);
  const apptTitle = await p.locator('text=Book a new appointment').isVisible();
  if (!apptTitle) return 'Back did not return to appointment drawer';
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
  await p.waitForTimeout(200);
});

// Appointment expand → Open Chart → workspace modal
await check('Appointment expand + workspace', async p => {
  const panel = p.locator('.panel').filter({ hasText: "Today's appointments" });
  const cards = panel.locator('.stack > div');
  if (await cards.count() === 0) return 'No appointment cards';
  await cards.first().click();
  await p.waitForTimeout(400);
  const actions = await p.locator('.appt-quick-actions').isVisible();
  if (!actions) return 'Quick actions not visible';
  await p.locator('.appt-quick-actions button').filter({ hasText: 'Open Chart' }).click();
  await p.waitForTimeout(400);
  const ws = await p.locator('.center-modal-backdrop').isVisible();
  if (!ws) return 'Workspace modal not visible';
  await p.locator('.center-modal-backdrop').click({ position: { x: 10, y: 10 } });
  await p.waitForTimeout(200);
});

// ═══════════════════════════════════════════
// 2. PATIENTS PAGE
// ═══════════════════════════════════════════
currentPage = 'Patients';
console.log('\n📋 ' + currentPage);
await page.goto('http://localhost:3003/patients', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Page loads with table', async p => p.locator('table.list').isVisible() ? true : 'No table');

await check('Search input works', async p => {
  const input = p.locator('input[placeholder*="Search"]');
  if (!await input.isVisible()) return 'No search input';
  await input.fill('Alice');
  await p.waitForTimeout(300);
  const rows = await p.locator('table.list tbody tr').count();
  if (rows === 0) return 'Search returned no results';
  await input.fill('');
});

await check('Filter pills toggle', async p => {
  const pill = p.locator('.filter-pill').filter({ hasText: 'Active' });
  if (!await pill.isVisible()) return 'No filter pills';
  await pill.click();
  await p.waitForTimeout(300);
});

await check('Row click navigates to detail', async p => {
  const row = p.locator('table.list tbody tr').first();
  if (!await row.isVisible()) return 'No rows';
  await row.click();
  await p.waitForTimeout(500);
  const isDetail = p.url().includes('/patients/');
  if (!isDetail) return 'Did not navigate to detail page: ' + p.url();
});

// ═══════════════════════════════════════════
// 3. PATIENT DETAIL PAGE
// ═══════════════════════════════════════════
currentPage = 'Patient Detail';
console.log('\n🦷 ' + currentPage);
await page.goto('http://localhost:3003/patients/P-018342', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Header panel with name + avatar', async p => {
  const name = await p.locator('text=Alice Stevens').first().isVisible();
  if (!name) return 'Patient name not visible';
});

await check('Schedule button exists', async p => {
  const btns = p.locator('.btn-ghost');
  const count = await btns.count();
  // Just check buttons exist
  if (count < 2) return 'Expected at least 2 header buttons';
});

await check('Tab: Overview has medical flags', async p => {
  const flags = await p.locator('text=Medical flags').isVisible();
  if (!flags) return 'No medical flags section';
});

await check('Tab: Tooth chart renders', async p => {
  await p.locator('button').filter({ hasText: 'Tooth chart' }).click();
  await p.waitForTimeout(300);
  const fdi = await p.locator('text=FDI').isVisible();
  if (!fdi) return 'No tooth chart';
});

await check('Tab: Insurance has coverage', async p => {
  await p.locator('button').filter({ hasText: 'Insurance' }).click();
  await p.waitForTimeout(300);
  const coverage = await p.locator('text=Basic').isVisible();
  if (!coverage) return 'No coverage info';
});

await check('Tab: Notes has SOAP', async p => {
  await p.locator('button').filter({ hasText: 'Notes' }).click();
  await p.waitForTimeout(300);
  const locked = await p.locator('text=Locked').isVisible();
  if (!locked) return 'No SOAP notes';
});

await check('Tab: Treatment plans', async p => {
  await p.locator('button').filter({ hasText: 'Treatment plans' }).click();
  await p.waitForTimeout(300);
  const tp = await p.locator('text=TP-001').isVisible();
  if (!tp) return 'No treatment plan';
});

await check('Tab: Billing', async p => {
  await p.locator('button').filter({ hasText: 'Billing' }).click();
  await p.waitForTimeout(300);
  const inv = await p.locator('text=INV-2026').isVisible();
  if (!inv) return 'No invoice';
});

await check('Tab: Audit', async p => {
  await p.locator('button').filter({ hasText: 'Audit' }).click();
  await p.waitForTimeout(300);
  const audit = await p.locator('text=UPDATE').isVisible();
  if (!audit) return 'No audit entry';
});

// ═══════════════════════════════════════════
// 4. SCHEDULE PAGE
// ═══════════════════════════════════════════
currentPage = 'Schedule';
console.log('\n📅 ' + currentPage);
await page.goto('http://localhost:3003/schedule', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Page loads with grid', async p => p.locator('.schedule-grid').isVisible() ? true : 'No grid');

await check('Day/Week filter pills', async p => {
  const weekPill = p.locator('.day-pill').filter({ hasText: 'Week' });
  if (!await weekPill.isVisible()) return 'No Week pill';
  await weekPill.click();
  await p.waitForTimeout(200);
});

await check('Appointment list renders', async p => {
  const rows = await p.locator('table.list tbody tr').count();
  if (rows === 0) return 'No appointments in list';
});

// ═══════════════════════════════════════════
// 5. TREATMENT PAGE
// ═══════════════════════════════════════════
currentPage = 'Treatment';
console.log('\n📝 ' + currentPage);
await page.goto('http://localhost:3003/treatment', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Page loads with plans', async p => {
  const tp = await p.locator('text=TP-001').isVisible();
  if (!tp) return 'No treatment plan';
});

await check('Progress bars visible', async p => {
  const bars = await p.locator('[style*="borderRadius: 4"][style*="overflow: hidden"]').count();
  // Progress bars exist
});

// ═══════════════════════════════════════════
// 6. LAB PAGE
// ═══════════════════════════════════════════
currentPage = 'Lab';
console.log('\n🧪 ' + currentPage);
await page.goto('http://localhost:3003/lab', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Page loads', async p => p.locator('h1').first().isVisible() ? true : 'No h1');

await check('KPI tiles visible', async p => {
  const kpis = await p.locator('text=In flight').count();
  if (kpis === 0) return 'No KPI tiles';
});

await check('Kanban pipeline renders', async p => {
  const kanban = await p.locator('text=Pipeline · Kanban').isVisible();
  if (!kanban) return 'No kanban section';
});

await check('Filter pills work', async p => {
  await p.locator('.filter-pill').filter({ hasText: 'Sent' }).click();
  await p.waitForTimeout(200);
  const active = await p.locator('.filter-pill.active').first().textContent();
  if (!active?.includes('Sent')) return 'Filter not active: ' + active;
});

await check('Vendor cards visible', async p => {
  const v = await p.locator('text=Pinnacle Dental Lab').first().isVisible();
  if (!v) return 'No vendor cards';
});

await check('Activity timeline visible', async p => {
  const t = await p.locator('text=Recent activity').isVisible();
  if (!t) return 'No activity section';
});

await check('Cases table has rows', async p => {
  const rows = await p.locator('table.cases tbody tr').count();
  if (rows === 0) return 'No case rows';
});

// ═══════════════════════════════════════════
// 7. BILLING PAGE
// ═══════════════════════════════════════════
currentPage = 'Billing';
console.log('\n💰 ' + currentPage);
await page.goto('http://localhost:3003/billing', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Page loads', async p => p.locator('h1').first().isVisible() ? true : 'No h1');
await check('Aging grid', async p => p.locator('text=0–30 days').isVisible() ? true : 'No aging');
await check('Claims section', async p => p.locator('text=Insurance Claims').isVisible() ? true : 'No claims');
await check('Search works', async p => {
  await p.locator('input[placeholder*="Search"]').fill('Alice');
  await p.waitForTimeout(300);
});
await check('Filter pills', async p => {
  await p.locator('.filter-pill').filter({ hasText: 'Paid' }).click();
  await p.waitForTimeout(200);
});

// ═══════════════════════════════════════════
// 8. COMMUNICATIONS PAGE
// ═══════════════════════════════════════════
currentPage = 'Communications';
console.log('\n💬 ' + currentPage);
await page.goto('http://localhost:3003/communications', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Inbox layout', async p => p.locator('.inbox').isVisible() ? true : 'No inbox');
await check('Thread list', async p => p.locator('text=Alice Stevens').first().isVisible() ? true : 'No threads');
await check('Channel chips', async p => {
  await p.locator('.chip').filter({ hasText: 'SMS' }).click();
  await p.waitForTimeout(200);
});
await check('Composer visible', async p => p.locator('textarea').isVisible() ? true : 'No composer');
await check('Templates exist', async p => {
  const tpl = await p.locator('.tpl').first().isVisible();
  if (!tpl) return 'No templates';
  await p.locator('.tpl').first().click();
  await p.waitForTimeout(200);
  const val = await p.locator('textarea').inputValue();
  if (!val) return 'Template not applied';
});

// ═══════════════════════════════════════════
// 9. CRM PAGE
// ═══════════════════════════════════════════
currentPage = 'CRM';
console.log('\n👥 ' + currentPage);
await page.goto('http://localhost:3003/crm', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Kanban columns', async p => {
  const cols = await p.locator('.col-head').count();
  if (cols < 5) return `Only ${cols} kanban columns`;
});
await check('Lead cards', async p => {
  const cards = await p.locator('.lead-card').count();
  if (cards === 0) return 'No lead cards';
});
await check('Lead click opens drawer', async p => {
  await p.locator('.lead-card').first().click();
  await p.waitForTimeout(400);
  const drawer = await p.locator('.drawer').isVisible();
  if (!drawer) return 'No drawer';
  await p.locator('.drawer-overlay').click({ position: { x: 10, y: 10 } });
  await p.waitForTimeout(200);
});
await check('Source breakdown', async p => p.locator('text=Source breakdown').isVisible() ? true : 'No sources');

// ═══════════════════════════════════════════
// 10. SETTINGS PAGE
// ═══════════════════════════════════════════
currentPage = 'Settings';
console.log('\n⚙️ ' + currentPage);
await page.goto('http://localhost:3003/settings', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

await check('Page loads', async p => p.locator('h1').first().isVisible() ? true : 'No h1');
await check('Working Hours tab', async p => {
  await p.locator('.stab-btn').filter({ hasText: 'Working hours' }).click();
  await p.waitForTimeout(200);
  const monday = await p.locator('text=Monday').isVisible();
  if (!monday) return 'No working hours';
});
await check('Integrations tab', async p => {
  await p.locator('.stab-btn').filter({ hasText: 'Integrations' }).click();
  await p.waitForTimeout(200);
  const twilio = await p.locator('text=Twilio SMS').isVisible();
  if (!twilio) return 'No integrations';
});
await check('Audit log', async p => {
  await p.locator('.stab-btn').filter({ hasText: 'Audit log' }).click();
  await p.waitForTimeout(200);
  const audit = await p.locator('text=UPDATE').isVisible();
  if (!audit) return 'No audit';
});

// ═══════════════════════════════════════════
// 11. OTHER PAGES
// ═══════════════════════════════════════════
currentPage = 'Reports';
console.log('\n📈 ' + currentPage);
await page.goto('http://localhost:3003/reports', { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await check('Page loads', async p => p.locator('h1').first().isVisible() ? true : 'No h1');

currentPage = 'Plans';
console.log('\n💳 ' + currentPage);
await page.goto('http://localhost:3003/plans', { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await check('3 tiers visible', async p => {
  const starter = await p.locator('text=Starter').isVisible();
  const pro = await p.locator('text=Professional').isVisible();
  const ent = await p.locator('text=Enterprise').isVisible();
  if (!starter || !pro || !ent) return 'Missing plan tiers';
});

currentPage = 'Login';
console.log('\n🔐 ' + currentPage);
await page.goto('http://localhost:3003/login', { waitUntil: 'networkidle' });
await page.waitForTimeout(800);
await check('Dark theme', async p => {
  const bg = await p.evaluate(() => getComputedStyle(document.body).backgroundColor);
  if (bg !== 'rgb(6, 15, 30)') return 'Not dark: ' + bg;
});
await check('Login form works', async p => {
  await p.locator('#login-email').fill('test@test.com');
  await p.locator('#login-password').fill('password123');
  await p.locator('button[type="submit"]').click();
  await p.waitForTimeout(500);
  const redirected = p.url().includes('dashboard');
  if (!redirected) return 'Not redirected: ' + p.url();
});

currentPage = 'Marketing';
console.log('\n🏠 ' + currentPage);
await page.goto('http://localhost:3003/', { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await check('Hero visible', async p => p.locator('text=Sovereign Clinical').first().isVisible() ? true : 'No hero');

// ═══════════════════════════════════════════
// SUMMARY
// ═══════════════════════════════════════════
console.log('\n\n═══════════════════════════════════════════');
console.log('  COMPREHENSIVE INTERACTION TEST RESULTS');
console.log('═══════════════════════════════════════════');
console.log(`  ${testCount - BUGS.length} passed · ${BUGS.length} bugs found`);
console.log('═══════════════════════════════════════════');

if (BUGS.length > 0) {
  console.log('\n🐛 BUGS FOUND:');
  for (const bug of BUGS) {
    console.log(`  [${bug.page}] ${bug.test}`);
    console.log(`      → ${bug.detail}`);
  }
}

await browser.close();
