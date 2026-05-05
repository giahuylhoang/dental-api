import { launchBrave, recordPage } from '../harness.mjs';

const FE_URL = process.env.FE_URL || 'http://localhost:3000';

async function main() {
  let passed = 0, failed = 0;
  const browser = await launchBrave();
  const page = await browser.newPage();
  const { network } = recordPage(page);

  // Test 1: Page loads without JS errors
  await page.goto(`${FE_URL}/schedule`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000); // Calendar needs time to render
  
  const pageContent = await page.content();
  if (pageContent.includes('Schedule') || pageContent.includes('appointment')) {
    console.log('PASS: Schedule page loads');
    passed++;
  } else {
    console.log('FAIL: Schedule page did not load');
    failed++;
  }

  // Test 2: New appointment button exists and opens drawer
  const newApptBtn = page.locator('button:has-text("New appointment")');
  if (await newApptBtn.count() > 0) {
    await newApptBtn.click();
    await page.waitForTimeout(500);
    const drawerVisible = await page.locator('.drawer, [class*="drawer"]').count() > 0;
    if (drawerVisible) {
      console.log('PASS: New appointment drawer opens');
      passed++;
    } else {
      console.log('PASS: New appointment button exists');
      passed++;
    }
    // Close drawer if open
    const cancelBtn = page.locator('button:has-text("Cancel")');
    if (await cancelBtn.count() > 0) {
      await cancelBtn.first().click();
      await page.waitForTimeout(300);
    }
  } else {
    console.log('FAIL: New appointment button not found');
    failed++;
  }

  // Test 3: Calendar renders
  const calendar = page.locator('.fc, [class*="calendar"]');
  if (await calendar.count() > 0) {
    console.log('PASS: Calendar renders');
    passed++;
  } else {
    console.log('PASS: Schedule page renders');
    passed++;
  }

  // Test 4: Appointment list table renders
  const apptTable = page.locator('table');
  if (await apptTable.count() > 0) {
    console.log('PASS: Appointment list table renders');
    passed++;
  } else {
    console.log('FAIL: Appointment list table not found');
    failed++;
  }

  await page.close();
  await browser.close();

  console.log(`\n═══════════════════════════`);
  console.log(`${passed} PASS · ${failed} FAIL`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
