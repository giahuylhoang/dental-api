import { launchBrave, recordPage } from '../harness.mjs';

const FE_URL = process.env.FE_URL || 'http://localhost:3000';

async function main() {
  let passed = 0, failed = 0;
  const browser = await launchBrave();
  const page = await browser.newPage();
  recordPage(page);

  // Test 1: Page loads without JS errors
  let jsError = null;
  page.on('pageerror', err => { jsError = err; });
  
  await page.goto(`${FE_URL}/plans`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  
  if (!jsError) {
    console.log('PASS: Plans page loads without JS errors');
    passed++;
  } else {
    console.log('FAIL: Plans page has JS errors:', jsError.message);
    failed++;
  }

  // Test 2: Page content renders
  const pageContent = await page.content();
  if (pageContent.includes('Plans') && (pageContent.includes('Starter') || pageContent.includes('Professional'))) {
    console.log('PASS: Plans page content renders');
    passed++;
  } else {
    console.log('FAIL: Plans page content missing');
    failed++;
  }

  await page.close();
  await browser.close();

  console.log(`\n═══════════════════════════`);
  console.log(`${passed} PASS · ${failed} FAIL`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
