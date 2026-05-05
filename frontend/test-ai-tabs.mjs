import { chromium } from 'playwright';

const BASE = 'http://localhost:3003';
const results = [];
const pass = (m) => { results.push(['PASS', m]); console.log('PASS', m); };
const fail = (m, err) => { results.push(['FAIL', m, err]); console.log('FAIL', m, err ?? ''); };

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const errs = [];
page.on('pageerror', e => errs.push(`pageerror: ${e.message}`));
page.on('console', m => { if (m.type() === 'error') errs.push(`console: ${m.text()}`); });

async function clickTab(label) {
  await page.locator(`.stab-btn:has-text("${label}")`).click();
  await page.waitForTimeout(150);
}

try {
  await page.goto(BASE + '/settings', { waitUntil: 'domcontentloaded' });

  // Confirm new tab labels exist (and the old ones don't).
  const expectTabs = ['Voice & Persona', 'AI Disclosure', 'Services', 'Knowledge'];
  const oldTabs = ['AI Greeting', 'AI Routing', 'AI Services', 'AI Knowledge'];
  for (const t of expectTabs) {
    const ok = await page.locator(`.stab-btn:has-text("${t}")`).count();
    if (ok) pass(`Tab present: ${t}`); else fail(`Tab missing: ${t}`);
  }
  for (const t of oldTabs) {
    const c = await page.locator(`.stab-btn:has-text("${t}")`).count();
    if (c === 0) pass(`Old tab gone: ${t}`); else fail(`Old tab still present: ${t}`);
  }

  // ── Voice & Persona ─────────────────────────────────────────────
  await clickTab('Voice & Persona');
  await page.waitForSelector('h2:has-text("Voice & persona")');
  // Initial: "All changes saved."
  const savedTextInitial = await page.locator('.save-bar .left').first().innerText();
  if (savedTextInitial.includes('All changes saved')) pass('Voice tab opens with All changes saved');
  else fail('Voice initial save state', savedTextInitial);

  // Edit assistant_name → save bar should switch to Unsaved changes
  const nameInput = page.locator('input.ai-input').first();
  await nameInput.fill('Aurora');
  await page.waitForTimeout(100);
  const dirtyText = await page.locator('.save-bar .left').first().innerText();
  if (dirtyText.includes('Unsaved changes')) pass('Voice dirty state triggers');
  else fail('Voice dirty did not trigger', dirtyText);

  // Save → back to All changes saved
  await page.locator('.save-bar .btn-row button:has-text("Save voice")').click();
  await page.waitForTimeout(200);
  const after = await page.locator('.save-bar .left').first().innerText();
  if (after.includes('All changes saved')) pass('Voice save resets dirty');
  else fail('Voice save did not reset', after);

  // Preview rail "Hear it back"
  const hearBtn = await page.locator('button:has-text("Hear it back")').count();
  if (hearBtn) pass('Voice preview rail has Hear it back button');
  else fail('Preview rail missing Hear it back');

  // ── AI Disclosure ────────────────────────────────────────────────
  await clickTab('AI Disclosure');
  await page.waitForSelector('h2:has-text("AI disclosure")');
  // Info banner
  const banner = await page.locator('.info-banner').count();
  if (banner) pass('Disclosure info banner renders'); else fail('Disclosure info banner missing');
  // Char counter shows "X / 280"
  const counter = await page.locator('.char-counter').first().innerText();
  if (/\d+ \/ 280 characters/.test(counter)) pass(`Disclosure char counter: ${counter}`);
  else fail('Disclosure char counter format', counter);
  // Required toggle works — input is visually hidden, click the visible track or use force.
  const req = page.locator('.toggle-row input[type="checkbox"]').first();
  const before = await req.isChecked();
  await page.locator('.toggle-row .pswitch-track').first().click();
  const afterReq = await req.isChecked();
  if (before !== afterReq) pass('Disclosure required toggle flips');
  else fail('Disclosure toggle did not flip');
  // Save bar transitions
  const dDirty = await page.locator('.save-bar .left').first().innerText();
  if (dDirty.includes('Unsaved changes')) pass('Disclosure save bar shows dirty');
  else fail('Disclosure dirty state', dDirty);
  await page.locator('.save-bar .btn-row button:has-text("Save disclosure")').click();
  await page.waitForTimeout(200);
  // Engineer-managed chip
  const chip = await page.locator('.ro-chip:has-text("Engineer-managed")').count();
  if (chip) pass('Disclosure shows Engineer-managed chip');
  else fail('Engineer-managed chip missing');

  // ── Services ─────────────────────────────────────────────────────
  await clickTab('Services');
  await page.waitForSelector('h2:has-text("The Service catalogue")');
  const rows = await page.locator('.svc-table tbody tr').count();
  if (rows >= 4) pass(`Services table has ${rows} rows`);
  else fail(`Services rows: ${rows}`);
  // Toggle the first service switch — click the visible track since input is sized 0×0.
  const firstSvcSwitch = page.locator('.svc-table tbody tr:first-child input[type="checkbox"]');
  await firstSvcSwitch.scrollIntoViewIfNeeded();
  const wasOn = await firstSvcSwitch.isChecked();
  await page.locator('.svc-table tbody tr:first-child .pswitch-track').click();
  await page.waitForTimeout(80);
  const isOn = await firstSvcSwitch.isChecked();
  if (wasOn !== isOn) pass('Services switch toggles');
  else fail('Services switch did not toggle');
  // First-row label updates
  const lbl = await page.locator('.svc-table tbody tr:first-child .toggle-cell span').last().innerText();
  if (/AI Bookable|Front-desk only/.test(lbl)) pass(`Services label updates: ${lbl}`);
  else fail('Services label format', lbl);

  // ── Knowledge ───────────────────────────────────────────────────
  await clickTab('Knowledge');
  await page.waitForSelector('h2:has-text("The Knowledge base")');
  const docCount = await page.locator('.doc-row').count();
  if (docCount >= 2) pass(`Knowledge shows ${docCount} doc rows`);
  else fail(`Knowledge doc count`, docCount);
  // Click a row to expand
  await page.locator('.doc-row').first().click();
  await page.waitForSelector('.doc-expand textarea', { timeout: 2000 });
  const ta = await page.locator('.doc-expand textarea').first();
  const txt = await ta.inputValue();
  if (txt.length > 20) pass('Knowledge expand shows body content');
  else fail('Knowledge body empty', txt);
  // Edit body
  await ta.fill('# Updated\n\nNew content.');
  // Collapse and re-expand: edited text should still be there
  await page.locator('.doc-row').first().click();
  await page.waitForTimeout(80);
  await page.locator('.doc-row').first().click();
  await page.waitForTimeout(80);
  const txt2 = await page.locator('.doc-expand textarea').first().inputValue();
  if (txt2.startsWith('# Updated')) pass('Knowledge body persists across collapse/expand');
  else fail('Knowledge edits lost', txt2.slice(0, 30));

} catch (e) { fail('Settings AI tabs', e.message); }

console.log('\n═══════════════════════════');
const passCount = results.filter(r => r[0] === 'PASS').length;
const failCount = results.filter(r => r[0] === 'FAIL').length;
console.log(`${passCount} PASS · ${failCount} FAIL`);
if (errs.length) {
  console.log(`\nPage errors (${errs.length}):`);
  errs.slice(0, 8).forEach(e => console.log('  ', e));
}
await browser.close();
process.exit(failCount > 0 ? 1 : 0);
