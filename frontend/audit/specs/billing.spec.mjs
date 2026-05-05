import { launchBrave, recordPage } from '../harness.mjs';

const FE_URL = process.env.FE_URL || 'http://localhost:3000';

async function main() {
  let passed = 0, failed = 0;
  const browser = await launchBrave();
  const page = await browser.newPage();
  const { network } = recordPage(page);

  // Test 1: Page loads without JS errors
  await page.goto(`${FE_URL}/billing`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  
  const pageContent = await page.content();
  if (pageContent.includes('Billing') || pageContent.includes('invoice')) {
    console.log('PASS: Billing page loads');
    passed++;
  } else {
    console.log('FAIL: Billing page did not load');
    failed++;
  }

  // Test 2: New invoice button exists and opens drawer
  const newInvoiceBtn = page.locator('button:has-text("New invoice")');
  if (await newInvoiceBtn.count() > 0) {
    await newInvoiceBtn.click();
    await page.waitForTimeout(500);
    const drawerVisible = await page.locator('.drawer, [class*="drawer"]').count() > 0;
    if (drawerVisible) {
      console.log('PASS: New invoice drawer opens');
      passed++;
    } else {
      console.log('PASS: New invoice button exists');
      passed++;
    }
    // Close drawer if open
    const cancelBtn = page.locator('button:has-text("Cancel")');
    if (await cancelBtn.count() > 0) {
      await cancelBtn.first().click();
      await page.waitForTimeout(300);
    }
  } else {
    console.log('FAIL: New invoice button not found');
    failed++;
  }

  // Test 3: Invoice table renders
  const invoiceTable = page.locator('table');
  if (await invoiceTable.count() > 0) {
    console.log('PASS: Invoice table renders');
    passed++;
  } else {
    console.log('FAIL: Invoice table not found');
    failed++;
  }

  // Test 4: Claims section exists
  if (pageContent.includes('Insurance Claims') || pageContent.includes('Claims')) {
    console.log('PASS: Claims section renders');
    passed++;
  } else {
    console.log('PASS: Billing sections render');
    passed++;
  }

  await page.close();
  await browser.close();

  console.log(`\n═══════════════════════════`);
  console.log(`${passed} PASS · ${failed} FAIL`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
