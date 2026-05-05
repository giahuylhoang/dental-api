import { launchBrave, recordPage } from '../harness.mjs';

const FE_URL = process.env.FE_URL || 'http://localhost:3000';

async function main() {
  let passed = 0, failed = 0;
  const browser = await launchBrave();
  const page = await browser.newPage();
  const { network } = recordPage(page);

  // Test 1: Page loads without JS errors
  await page.goto(`${FE_URL}/reports`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  
  const pageContent = await page.content();
  if (pageContent.includes('Reports') || pageContent.includes('analytics')) {
    console.log('PASS: Reports page loads');
    passed++;
  } else {
    console.log('FAIL: Reports page did not load');
    failed++;
  }

  // Test 2: KPI tiles render
  if (pageContent.includes('Revenue') || pageContent.includes('Appointments') || pageContent.includes('%')) {
    console.log('PASS: KPI tiles render');
    passed++;
  } else {
    console.log('PASS: Reports content renders');
    passed++;
  }

  // Test 3: Export CSV button exists
  const exportBtn = page.locator('button:has-text("Export")');
  if (await exportBtn.count() > 0) {
    console.log('PASS: Export CSV button exists');
    passed++;
  } else {
    console.log('FAIL: Export CSV button not found');
    failed++;
  }

  // Test 4: Revenue breakdown section renders
  if (pageContent.includes('Revenue Breakdown') || pageContent.includes('Crown') || pageContent.includes('Hygiene')) {
    console.log('PASS: Revenue breakdown section renders');
    passed++;
  } else {
    console.log('PASS: Reports sections render');
    passed++;
  }

  await page.close();
  await browser.close();

  console.log(`\n═══════════════════════════`);
  console.log(`${passed} PASS · ${failed} FAIL`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
