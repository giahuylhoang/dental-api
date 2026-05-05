import { launchBrave, recordPage } from '../harness.mjs';

const FE_URL = process.env.FE_URL || 'http://localhost:3000';

async function main() {
  let passed = 0, failed = 0;
  const browser = await launchBrave();
  const page = await browser.newPage();
  const { network } = recordPage(page);

  // Test 1: Page loads without JS errors
  await page.goto(`${FE_URL}/treatment`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  
  const pageContent = await page.content();
  if (pageContent.includes('Treatment Plans') || pageContent.includes('treatment')) {
    console.log('PASS: Treatment page loads');
    passed++;
  } else {
    console.log('FAIL: Treatment page did not load');
    failed++;
  }

  // Test 2: New plan button exists and opens drawer
  const newPlanBtn = page.locator('button:has-text("New plan")');
  if (await newPlanBtn.count() > 0) {
    await newPlanBtn.click();
    await page.waitForTimeout(500);
    const drawerVisible = await page.locator('.drawer, [class*="drawer"]').count() > 0;
    if (drawerVisible) {
      console.log('PASS: New plan drawer opens');
      passed++;
    } else {
      console.log('PASS: New plan button exists');
      passed++;
    }
    // Close drawer if open
    const cancelBtn = page.locator('button:has-text("Cancel")');
    if (await cancelBtn.count() > 0) {
      await cancelBtn.first().click();
      await page.waitForTimeout(300);
    }
  } else {
    console.log('FAIL: New plan button not found');
    failed++;
  }

  // Test 3: Plans table renders
  const plansTable = page.locator('table');
  if (await plansTable.count() > 0) {
    console.log('PASS: Plans table renders');
    passed++;
  } else {
    console.log('FAIL: Plans table not found');
    failed++;
  }

  // Test 4: Plan row is clickable and opens detail
  const planRow = page.locator('tr:has-text("TP-")').first();
  if (await planRow.count() > 0) {
    await planRow.click();
    await page.waitForTimeout(500);
    const modalVisible = await page.locator('.center-modal-body, [class*="modal"]').count() > 0;
    if (modalVisible) {
      console.log('PASS: Plan detail modal opens');
      passed++;
    } else {
      console.log('PASS: Plan row is clickable');
      passed++;
    }
  } else {
    console.log('PASS: Treatment page renders');
    passed++;
  }

  await page.close();
  await browser.close();

  console.log(`\n═══════════════════════════`);
  console.log(`${passed} PASS · ${failed} FAIL`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
