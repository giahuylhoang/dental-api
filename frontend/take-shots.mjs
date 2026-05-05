import { chromium } from 'playwright';
const BASE = 'http://localhost:3003';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
await page.goto(BASE + '/settings', { waitUntil: 'domcontentloaded' });

for (const t of ['Voice & Persona', 'AI Disclosure', 'Services', 'Knowledge']) {
  await page.locator(`.stab-btn:has-text("${t}")`).click();
  await page.waitForTimeout(250);
  const slug = t.toLowerCase().replace(/[^a-z]+/g, '-');
  await page.screenshot({ path: `/tmp/settings-${slug}.png`, fullPage: true });
  console.log(`saved /tmp/settings-${slug}.png`);
}

// Also capture the Knowledge tab with one row expanded
await page.locator('.stab-btn:has-text("Knowledge")').click();
await page.waitForTimeout(150);
await page.locator('.doc-row').first().click();
await page.waitForTimeout(200);
await page.screenshot({ path: '/tmp/settings-knowledge-open.png', fullPage: true });
console.log('saved /tmp/settings-knowledge-open.png');

await browser.close();
