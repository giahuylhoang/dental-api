/**
 * Frontend ↔ Backend integration smoke test.
 *
 * Assumes:
 *   - dental-api FastAPI on http://localhost:8001 with seeded demo data
 *     (run `./run_local.sh` or `python scripts/sync_db.py` + `python run_api.py`).
 *   - Next dev server on http://localhost:3000 with NEXT_PUBLIC_API_BASE
 *     pointing at the backend.
 *
 * Verifies:
 *   - Settings → Voice & Persona renders the seeded "Aurora" assistant_name
 *   - Settings → AI Disclosure renders the seeded phrase + sets required toggle
 *   - Settings → Services renders the seeded bookable flags
 *   - Settings → Knowledge renders the 3 seeded docs
 *   - Patients page renders the 6 seeded patients
 */
import { chromium } from 'playwright';

const FE = process.env.FE_URL || 'http://localhost:3000';
const results = [];
const pass = (m) => { results.push(['PASS', m]); console.log('PASS', m); };
const fail = (m, err) => { results.push(['FAIL', m, err]); console.log('FAIL', m, err ?? ''); };

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const errs = [];
page.on('pageerror', e => errs.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

async function clickTab(label) {
  await page.locator(`.stab-btn:has-text("${label}")`).click();
  await page.waitForTimeout(400);
}

try {
  await page.goto(FE + '/settings', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.stab-btn', { timeout: 5000 });

  // Voice & Persona — should hydrate to "Aurora"
  await clickTab('Voice & Persona');
  await page.waitForSelector('[data-testid="voice-panel"][data-loaded="true"]', { timeout: 5000 });
  const assistantName = await page.locator('input.ai-input').first().inputValue();
  if (assistantName === 'Aurora') pass('Voice tab hydrates assistant_name from API: Aurora');
  else fail('Voice did not hydrate from API', `got: ${assistantName}`);

  // Save propagates: change to Echo, save, reload, expect Echo
  await page.locator('input.ai-input').first().fill('Echo');
  await page.locator('button:has-text("Save voice")').click();
  await page.waitForTimeout(400);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.stab-btn', { timeout: 5000 });
  await clickTab('Voice & Persona');
  await page.waitForSelector('[data-testid="voice-panel"][data-loaded="true"]', { timeout: 5000 });
  const echoName = await page.locator('input.ai-input').first().inputValue();
  if (echoName.toLowerCase() === 'echo') pass('Voice save round-trips through API (Echo persists across reload)');
  else fail('Voice save round-trip', `got: ${echoName}`);

  // AI Disclosure — phrase should hydrate
  await clickTab('AI Disclosure');
  await page.waitForSelector('[data-testid="disclosure-panel"][data-loaded="true"]', { timeout: 5000 });
  const discPhrase = await page.locator('textarea.ai-textarea').inputValue();
  if (discPhrase.includes('AI receptionist')) pass('Disclosure phrase hydrates from API');
  else fail('Disclosure phrase', `got: ${discPhrase}`);

  // Services — first row should be 'Routine Cleaning' (id=1) marked bookable
  await clickTab('Services');
  await page.waitForSelector('[data-testid="services-panel"][data-loaded="true"]', { timeout: 5000 });
  await page.waitForSelector('.svc-table tbody tr');
  const firstRowName = await page.locator('.svc-table tbody tr:first-child td:nth-child(2)').innerText();
  const firstRowChecked = await page.locator('.svc-table tbody tr:first-child input[type="checkbox"]').isChecked();
  if (firstRowName.includes('Routine Cleaning') && firstRowChecked) pass('Services hydrates and first row is bookable');
  else fail('Services hydration', `name=${firstRowName} checked=${firstRowChecked}`);

  // Knowledge — should show 3 docs from the seed
  await clickTab('Knowledge');
  await page.waitForSelector('[data-testid="knowledge-panel"][data-loaded="true"]', { timeout: 5000 });
  await page.waitForSelector('.doc-row');
  const docCount = await page.locator('.doc-row').count();
  if (docCount === 3) pass(`Knowledge shows 3 seeded docs`);
  else fail(`Knowledge doc count`, `got ${docCount}`);

  // Patients page — should show the 6 seeded patients
  await page.goto(FE + '/patients', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(
    () => document.querySelectorAll('.list tbody tr').length >= 6,
    null,
    { timeout: 6000 },
  );
  const rowCount = await page.locator('.list tbody tr').count();
  if (rowCount >= 6) pass(`Patients page shows ${rowCount} rows from API`);
  else fail('Patients page row count', `got ${rowCount}`);

} catch (e) {
  fail('Integration test', e.message);
}

console.log('\n═══════════════════════════');
const passCount = results.filter(r => r[0] === 'PASS').length;
const failCount = results.filter(r => r[0] === 'FAIL').length;
console.log(`${passCount} PASS · ${failCount} FAIL`);
if (errs.length) {
  console.log(`\nPage errors (${errs.length}):`);
  errs.slice(0, 10).forEach(e => console.log('  ', e));
}
await browser.close();
process.exit(failCount > 0 ? 1 : 0);
