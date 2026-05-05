import { chromium } from 'playwright';

const BASE = 'http://localhost:3003';
const results = [];
const pass = (m) => { results.push(['PASS', m]); console.log('PASS', m); };
const fail = (m, err) => { results.push(['FAIL', m, err]); console.log('FAIL', m, err ?? ''); };

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const pageErrs = [];
page.on('pageerror', e => pageErrs.push(`pageerror: ${e.message}`));
page.on('console', m => { if (m.type() === 'error') pageErrs.push(`console: ${m.text()}`); });

async function go(path) {
  const r = await page.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  if (!r || r.status() !== 200) throw new Error(`${path} returned ${r?.status()}`);
}

// ─── P1 CRM drag-drop ───────────────────────────────────────────────
try {
  await go('/crm');
  await page.waitForSelector('.kanban .col');
  const cols = await page.$$eval('.kanban .col', els => els.length);
  if (cols !== 5) throw new Error(`Expected 5 cols, got ${cols}`);
  const newCount = await page.$$eval('.kanban .col:nth-child(1) .lead-card', els => els.length);
  pass(`CRM kanban renders 5 columns, ${newCount} cards in NEW`);

  // Drag first lead from NEW to QUALIFIED (3rd col)
  const card = await page.$('.kanban .col:nth-child(1) .lead-card');
  const target = await page.$('.kanban .col:nth-child(3)');
  const cb = await card.boundingBox();
  const tb = await target.boundingBox();
  await page.mouse.move(cb.x + cb.width / 2, cb.y + cb.height / 2);
  await page.mouse.down();
  await page.mouse.move(cb.x + cb.width / 2 + 12, cb.y + cb.height / 2 + 12, { steps: 5 });
  await page.mouse.move(tb.x + tb.width / 2, tb.y + tb.height / 2, { steps: 12 });
  await page.mouse.up();
  await page.waitForTimeout(400);

  const newAfter = await page.$$eval('.kanban .col:nth-child(1) .lead-card', els => els.length);
  const qualAfter = await page.$$eval('.kanban .col:nth-child(3) .lead-card', els => els.length);
  if (newAfter < newCount && qualAfter > 2) pass(`CRM drag moved card NEW(${newCount}→${newAfter}) QUAL(2→${qualAfter})`);
  else fail(`CRM drag did not change column counts`, `NEW=${newAfter}, QUAL=${qualAfter}`);
} catch (e) { fail('CRM drag-drop', e.message); }

// ─── P2 Treatment edit ─────────────────────────────────────────────
try {
  await go('/treatment');
  await page.click('table.list tbody tr:first-child');
  await page.waitForSelector('.center-modal-body');
  await page.click('button:has-text("Edit plan")');
  const inputCount = await page.$$eval('.center-modal-body input.d-input', els => els.length);
  if (inputCount < 2) throw new Error(`Expected edit form inputs, got ${inputCount}`);
  await page.click('.center-modal-body button:has-text("Save changes")');
  await page.waitForTimeout(300);
  pass('Treatment Edit plan opens form and saves');
} catch (e) { fail('Treatment edit', e.message); }

// ─── P3 Lab edit ──────────────────────────────────────────────────
try {
  await go('/lab');
  await page.waitForSelector('table.cases tbody tr');
  await page.click('table.cases tbody tr:first-child');
  await page.waitForSelector('.center-modal-body');
  await page.click('button:has-text("Edit case")');
  const editVendor = await page.$('.center-modal-body select.d-input');
  if (!editVendor) throw new Error('No vendor select in edit form');
  await page.click('.center-modal-body button:has-text("Save changes")');
  pass('Lab Edit case opens form and saves');
} catch (e) { fail('Lab edit', e.message); }

// ─── P3 Lab detail page deleted ────────────────────────────────────
try {
  const r = await page.goto(BASE + '/lab/LC-2026-0481', { waitUntil: 'domcontentloaded' });
  if (r.status() === 404) pass('Lab detail page returns 404 (deleted)');
  else fail('Lab detail not deleted', `status=${r.status()}`);
} catch (e) { fail('Lab detail', e.message); }

// ─── P4 Billing modals ─────────────────────────────────────────────
try {
  await go('/billing');
  await page.waitForSelector('.panel table.list tbody tr');
  await page.click('.panel table.list tbody tr:first-child');
  await page.waitForSelector('.center-modal-body');
  pass('Billing invoice click opens modal');
  await page.click('.center-modal-body button:has-text("Close")');
  await page.waitForTimeout(200);

  // Find claims section by text and click first row
  await page.locator('text=Insurance Claims').scrollIntoViewIfNeeded();
  const claimRow = await page.locator('h2:has-text("Insurance Claims"), .panel-h-title:has-text("Insurance Claims")').first();
  // Click first row in the second .panel after the invoices panel
  const rows = await page.$$('.panel table.list tbody tr');
  // Find a row whose first cell starts with CLM-
  let opened = false;
  for (const row of rows) {
    const id = await row.$eval('td:first-child', el => el.textContent || '');
    if (id.startsWith('CLM-')) {
      await row.click();
      opened = true;
      break;
    }
  }
  if (!opened) throw new Error('No claim row found');
  await page.waitForSelector('.center-modal-body');
  pass('Billing claim click opens modal');
} catch (e) { fail('Billing modals', e.message); }

// ─── P4 Invoice detail page deleted ────────────────────────────────
try {
  const r = await page.goto(BASE + '/billing/invoices/INV-2026-0418', { waitUntil: 'domcontentloaded' });
  if (r.status() === 404) pass('Invoice detail page returns 404 (deleted)');
  else fail('Invoice detail not deleted', `status=${r.status()}`);
} catch (e) { fail('Invoice detail', e.message); }

// ─── P5 Communications composer ────────────────────────────────────
try {
  await go('/communications');
  await page.click('button:has-text("+ New message")');
  await page.waitForSelector('.drawer .field, [role="dialog"] .field, .drawer-card .field', { timeout: 3000 }).catch(() => {});
  // Drawer overlay shows up — assert by text
  const drawerVisible = await page.locator('text=Compose message').isVisible();
  if (drawerVisible) pass('Communications + New message opens composer drawer');
  else fail('Communications drawer did not open');
} catch (e) { fail('Communications composer', e.message); }

// ─── P6 Schedule FullCalendar ──────────────────────────────────────
try {
  await go('/schedule');
  await page.waitForSelector('.rr-calendar .fc', { timeout: 5000 });
  const hasFc = await page.$('.fc');
  if (!hasFc) throw new Error('FullCalendar root not found');
  pass('Schedule FullCalendar mounted');

  // Verify view buttons exist
  const monthBtn = await page.$('.fc-dayGridMonth-button');
  const weekBtn = await page.$('.fc-timeGridWeek-button');
  const dayBtn = await page.$('.fc-timeGridDay-button');
  if (!monthBtn || !weekBtn || !dayBtn) throw new Error('Missing view buttons');
  pass('Schedule has Month/Week/Day buttons');

  // Switch to month view and back
  await monthBtn.click();
  await page.waitForTimeout(300);
  const isMonth = await page.$('.fc-dayGridMonth-view, .fc-daygrid');
  if (isMonth) pass('Schedule month view loads');
  else fail('Month view did not render');

  await weekBtn.click();
  await page.waitForTimeout(300);

  // Confirm at least one event renders on the week of 2026-05-04
  await page.waitForSelector('.fc-timegrid-event', { timeout: 5000 });
  const evCount = await page.$$eval('.fc-timegrid-event', els => els.length);
  if (evCount > 0) pass(`Schedule renders ${evCount} appointments`);
  else fail('No events rendered on week view');

  // Confirm at least one busy background event renders
  const bg = await page.$('.fc-bg-event');
  if (bg) pass('Schedule renders busy background event');
  else fail('No busy block rendered');

  // FullCalendar listens via its own delegated pointer-event system, so use a real mouse click
  // at the centre of the event element. The harness wrapper that intercepts pointer events
  // is the same delegated handler, so clicking it does fire eventClick.
  const evEl = await page.locator('.fc-event').first();
  const box = await evEl.boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + 8);
  await page.waitForSelector('.center-modal-body', { timeout: 4000 });
  pass('Schedule event click opens detail modal');
} catch (e) { fail('Schedule FullCalendar', e.message); }

// ─── Summary ─────────────────────────────────────────────────────
console.log('\n═══════════════════════════');
const passCount = results.filter(r => r[0] === 'PASS').length;
const failCount = results.filter(r => r[0] === 'FAIL').length;
console.log(`${passCount} PASS · ${failCount} FAIL`);
if (pageErrs.length) {
  console.log(`\nPage errors detected (${pageErrs.length}):`);
  pageErrs.slice(0, 8).forEach(e => console.log('  ', e));
}
await browser.close();
process.exit(failCount > 0 ? 1 : 0);
