import { launchBrave, recordPage } from './harness.mjs';
import { writeFileSync, mkdirSync } from 'fs';

const ROUTES = ['/dashboard', '/patients', '/schedule', '/treatment', '/plans', '/lab', '/billing', '/crm', '/communications', '/reports', '/settings'];
const FE_URL = process.env.FE_URL || 'http://localhost:3000';

async function main() {
  const browser = await launchBrave();
  const deadButtons = [];

  for (const route of ROUTES) {
    const page = await browser.newPage();
    const { network } = recordPage(page);
    
    await page.goto(`${FE_URL}${route}`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    const buttons = await page.locator('button, [role=button], [draggable=true]').all();
    
    for (const btn of buttons) {
      try {
        const auditAttr = await btn.getAttribute('data-audit');
        if (auditAttr === 'local-only') continue;

        const isVisible = await btn.isVisible();
        if (!isVisible) continue;

        const text = (await btn.textContent())?.trim().slice(0, 50) || '';
        const selector = await btn.evaluate(el => {
          if (el.id) return `#${el.id}`;
          if (el.getAttribute('data-testid')) return `[data-testid="${el.getAttribute('data-testid')}"]`;
          const classes = el.className?.split?.(' ')?.filter(c => c && !c.includes(':'))?.slice(0, 2)?.join('.') || '';
          return classes ? `.${classes}` : el.tagName.toLowerCase();
        });

        const networkBefore = network.length;
        const urlBefore = page.url();

        try {
          await btn.click({ timeout: 1000 });
          await page.waitForTimeout(1000);
        } catch { continue; }

        const urlAfter = page.url();
        const networkAfter = network.length;
        const hadApiCall = network.slice(networkBefore).some(n => n.url.includes('/api/'));
        const navigated = urlAfter !== urlBefore;

        if (!hadApiCall && !navigated) {
          deadButtons.push({ page: route, selector, text, why: 'no-api-no-nav' });
        }

        // Reset page state
        if (navigated) {
          await page.goto(`${FE_URL}${route}`, { waitUntil: 'networkidle' });
          await page.waitForTimeout(300);
        }
      } catch {}
    }
    await page.close();
  }

  await browser.close();

  mkdirSync('audit/out', { recursive: true });
  writeFileSync('audit/out/dead-buttons.json', JSON.stringify(deadButtons, null, 2));
  console.log(`Found ${deadButtons.length} dead buttons`);
}

main().catch(e => { console.error(e); process.exit(1); });
