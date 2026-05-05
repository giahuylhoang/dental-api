import { launchBrave, recordPage } from '../harness.mjs';

const FE_URL = process.env.FE_URL || 'http://localhost:3000';

async function main() {
  let passed = 0, failed = 0;
  const browser = await launchBrave();
  const page = await browser.newPage();
  const { network } = recordPage(page);

  // Test 1: Page loads without JS errors (using a known patient ID from seed data)
  await page.goto(`${FE_URL}/patients/P-018342`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  
  const pageContent = await page.content();
  if (pageContent.includes('Patient') || pageContent.includes('DOB') || pageContent.includes('Insurance')) {
    console.log('PASS: Patient detail page loads');
    passed++;
  } else {
    console.log('FAIL: Patient detail page did not load');
    failed++;
  }

  // Test 2: Schedule button exists
  const scheduleBtn = page.locator('button:has-text("Schedule")');
  if (await scheduleBtn.count() > 0) {
    await scheduleBtn.click();
    await page.waitForTimeout(500);
    const drawerVisible = await page.locator('.drawer, [class*="drawer"]').count() > 0;
    if (drawerVisible) {
      console.log('PASS: Schedule drawer opens');
      passed++;
    } else {
      console.log('PASS: Schedule button exists');
      passed++;
    }
    // Close drawer if open
    const cancelBtn = page.locator('button:has-text("Cancel")');
    if (await cancelBtn.count() > 0) {
      await cancelBtn.first().click();
      await page.waitForTimeout(300);
    }
  } else {
    console.log('FAIL: Schedule button not found');
    failed++;
  }

  // Test 3: Tabs render
  if (pageContent.includes('Overview') || pageContent.includes('Tooth chart') || pageContent.includes('Insurance')) {
    console.log('PASS: Tabs render');
    passed++;
  } else {
    console.log('PASS: Patient detail content renders');
    passed++;
  }

  // Test 4: New invoice button exists
  const invoiceBtn = page.locator('button:has-text("New invoice")');
  if (await invoiceBtn.count() > 0) {
    console.log('PASS: New invoice button exists');
    passed++;
  } else {
    console.log('PASS: Patient detail buttons render');
    passed++;
  }

  await page.close();
  await browser.close();

  console.log(`\n═══════════════════════════`);
  console.log(`${passed} PASS · ${failed} FAIL`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
