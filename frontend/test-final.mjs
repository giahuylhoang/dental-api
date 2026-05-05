import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
let passed = 0, failed = 0;
const results = [];

const T = async (name, url, checks) => {
  try {
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);
    for (const { fn, desc } of checks) {
      const ok = await fn(page);
      if (!ok) throw new Error(desc);
    }
    results.push('✅ ' + name);
    passed++;
  } catch(e) {
    results.push('❌ ' + name + ' — ' + e.message.slice(0, 80));
    failed++;
  }
};

// 1. Dashboard
await T('Dashboard', 'http://localhost:3003/dashboard', [
  { desc: 'Page title visible', fn: p => p.locator('h1').first().isVisible() },
  { desc: 'KPI tiles render', fn: p => p.locator('text=Schedule fill').isVisible() },
  { desc: 'Appointments list', fn: p => p.locator('.stack').first().isVisible() },
  { desc: 'Lab pipeline panel', fn: p => p.locator('text=Lab pipeline').first().isVisible() },
  { desc: 'Recent patients panel', fn: p => p.locator('text=Recent patients').isVisible() },
  { desc: 'Recent invoices table', fn: p => p.locator('.recent-table').isVisible() },
]);

// 2. Login
await T('Login (dark theme)', 'http://localhost:3003/login', [
  { desc: 'Welcome back header', fn: p => p.locator('text=Welcome back').isVisible() },
  { desc: 'Dark background', fn: async p => { const bg = await p.evaluate(() => getComputedStyle(document.body).backgroundColor); return bg === 'rgb(6, 15, 30)'; } },
  { desc: 'Login form inputs', fn: p => p.locator('#login-email').isVisible() },
  { desc: 'Submit button', fn: p => p.locator('button[type="submit"]').isVisible() },
]);

// 3. Marketing
await T('Marketing landing', 'http://localhost:3003/', [
  { desc: 'Hero headline', fn: p => p.locator('text=Sovereign Clinical').first().isVisible() },
  { desc: 'Nav bar', fn: p => p.locator('text=Schedule a demo').first().isVisible() },
  { desc: 'Three Pillars', fn: p => p.locator('text=One system').isVisible() },
  { desc: 'CTA section', fn: p => p.locator('text=See the system').isVisible() },
]);

// 4. Patient detail
await T('Patient detail', 'http://localhost:3003/patients/P-018342', [
  { desc: 'Patient name', fn: p => p.locator('text=Alice Stevens').first().isVisible() },
  { desc: 'Overview tab', fn: p => p.locator('text=Medical flags').isVisible() },
  { desc: '9 tabs visible', fn: async p => (await p.locator('button').filter({ hasText: /Overview|Tooth chart|Insurance|Documents|Notes|Treatment|Communications|Billing|Audit/ }).count()) >= 9 },
]);

// 5. Lab
await T('Lab pipeline', 'http://localhost:3003/lab', [
  { desc: 'Page title', fn: p => p.locator('text=Lab pipeline').first().isVisible() },
  { desc: 'KPI tiles', fn: p => p.locator('text=In flight').isVisible() },
  { desc: 'Kanban section', fn: p => p.locator('text=Pipeline').first().isVisible() },
  { desc: 'Filter pills', fn: p => p.locator('.filter-pill').first().isVisible() },
  { desc: 'Vendors grid', fn: p => p.locator('text=Pinnacle Dental Lab').first().isVisible() },
  { desc: 'Activity timeline', fn: p => p.locator('text=Recent activity').isVisible() },
]);

// 6. Billing
await T('Billing', 'http://localhost:3003/billing', [
  { desc: 'Revenue KPIs', fn: p => p.locator('text=Total Revenue').isVisible() },
  { desc: 'Aging grid', fn: p => p.locator('text=0–30 days').isVisible() },
  { desc: 'Invoices table', fn: p => p.locator('text=INV-2026').first().isVisible() },
  { desc: 'Claims section', fn: p => p.locator('text=Insurance Claims').isVisible() },
]);

// 7. Communications
await T('Communications', 'http://localhost:3003/communications', [
  { desc: 'Thread list', fn: p => p.locator('text=Alice Stevens').first().isVisible() },
  { desc: 'Channel chips', fn: p => p.locator('.chip').first().isVisible() },
  { desc: 'Message area', fn: p => p.locator('.msg').first().isVisible() },
  { desc: 'Composer textarea', fn: p => p.locator('textarea').isVisible() },
  { desc: 'Templates', fn: p => p.locator('text=Appointment reminder').isVisible() },
]);

// 8. CRM
await T('CRM', 'http://localhost:3003/crm', [
  { desc: '5 kanban columns', fn: async p => (await p.locator('.col-head').count()) >= 5 },
  { desc: 'Lead cards', fn: p => p.locator('.lead-card').first().isVisible() },
  { desc: 'Source breakdown', fn: p => p.locator('text=Source breakdown').isVisible() },
]);

// 9. Settings
await T('Settings', 'http://localhost:3003/settings', [
  { desc: '12 tabs', fn: async p => (await p.locator('button').filter({ hasText: /Clinic info|Working|Operatories|Providers|Users|Integrations|Notifications|Audit|Greeting|Routing|Services|Knowledge/ }).count()) >= 12 },
  { desc: 'Clinic info form', fn: p => p.locator('input[value="Oak Dental Calgary"]').isVisible() },
]);

// 10. Schedule
await T('Schedule', 'http://localhost:3003/schedule', [
  { desc: 'Page loaded', fn: p => p.locator('h1').first().isVisible() },
  { desc: 'Day/Week pills', fn: p => p.locator('text=Week').isVisible() },
]);

// 11. Treatment
await T('Treatment', 'http://localhost:3003/treatment', [
  { desc: 'Plans table', fn: p => p.locator('text=Treatment Plans').first().isVisible() },
]);

// 12. Reports
await T('Reports', 'http://localhost:3003/reports', [
  { desc: 'Revenue breakdown', fn: p => p.locator('text=Revenue Breakdown').isVisible() },
]);

// 13. Plans
await T('Plans', 'http://localhost:3003/plans', [
  { desc: '3 tiers', fn: p => p.locator('text=Starter').isVisible() },
  { desc: 'Professional', fn: p => p.locator('text=Professional').isVisible() },
  { desc: 'Enterprise', fn: p => p.locator('text=Enterprise').isVisible() },
]);

console.log('\n═══════════════════════════');
for (const r of results) console.log(r);
console.log('═══════════════════════════');
console.log(`  ${passed} passed · ${failed} failed  (${Math.round(passed/(passed+failed)*100)}%)`);
console.log('═══════════════════════════');

await browser.close();
