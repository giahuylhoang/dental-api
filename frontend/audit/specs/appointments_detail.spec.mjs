import { launchBrave, recordPage } from '../harness.mjs';

const FE_URL = process.env.FE_URL || 'http://localhost:3000';
const API_BASE = process.env.API_BASE || 'http://localhost:8001';

async function createTestAppointment() {
  const patientRes = await fetch(`${API_BASE}/api/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Clinic-Id': 'default' },
    body: JSON.stringify({ first_name: 'Test', last_name: 'Patient', phone: '555-' + Date.now() }),
  });
  const patient = await patientRes.json();
  if (!patient.id) throw new Error('Failed to create patient');

  // Use a time slot far in the future to avoid conflicts
  const start = new Date(Date.now() + 86400000 * 30 + Math.random() * 86400000).toISOString();
  const end = new Date(new Date(start).getTime() + 3600000).toISOString();
  
  const apptRes = await fetch(`${API_BASE}/api/calendar/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Clinic-Id': 'default' },
    body: JSON.stringify({
      start_time: start,
      end_time: end,
      patient_id: patient.id,
      provider_id: 1,
      service_id: 1,
      reason: 'Test appointment',
      patient_name: 'Test Patient',
      service_name: 'Cleaning',
    }),
  });
  const appt = await apptRes.json();
  if (!appt.appointment_id) throw new Error('Failed to create appointment: ' + JSON.stringify(appt));
  return appt.appointment_id;
}

async function main() {
  let passed = 0, failed = 0;
  const browser = await launchBrave();
  
  const apptId = await createTestAppointment();
  console.log(`Created test appointment: ${apptId}`);

  const page = await browser.newPage();
  const { network } = recordPage(page);

  // Test 1: Page loads and hydrates
  await page.goto(`${FE_URL}/appointments/${apptId}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  
  const pageContent = await page.content();
  const hasApptData = pageContent.includes('Test Patient') || pageContent.includes(apptId);
  if (hasApptData) {
    console.log('PASS: Appointment detail hydrates from API');
    passed++;
  } else {
    console.log('FAIL: Appointment detail did not hydrate');
    failed++;
  }

  // Test 2: Confirm button triggers API call
  const confirmBtn = page.locator('[data-testid="btn-confirm"]');
  if (await confirmBtn.count() > 0) {
    const networkBefore = network.length;
    await confirmBtn.click();
    await page.waitForTimeout(1500);
    
    const confirmCall = network.slice(networkBefore).find(n => n.url.includes('/status') && n.method === 'PUT');
    if (confirmCall && confirmCall.status === 200) {
      console.log('PASS: Confirm button triggers status API call');
      passed++;
    } else {
      console.log('FAIL: Confirm button did not trigger API call');
      failed++;
    }
  } else {
    console.log('FAIL: Confirm button not found');
    failed++;
  }

  // Test 3: Check-in button triggers API call (need fresh appointment since we confirmed)
  // Reload page to get fresh state
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  
  const checkinBtn = page.locator('[data-testid="btn-checkin"]');
  if (await checkinBtn.count() > 0) {
    const networkBefore = network.length;
    await checkinBtn.click();
    await page.waitForTimeout(1500);
    
    const checkinCall = network.slice(networkBefore).find(n => n.url.includes('/status') && n.method === 'PUT');
    if (checkinCall) {
      console.log('PASS: Check-in button triggers status API call');
      passed++;
    } else {
      console.log('FAIL: Check-in button did not trigger API call');
      failed++;
    }
  } else {
    console.log('FAIL: Check-in button not found');
    failed++;
  }

  // Test 4: Cancel button triggers API call
  const cancelBtn = page.locator('[data-testid="btn-cancel"]');
  if (await cancelBtn.count() > 0) {
    const networkBefore = network.length;
    await cancelBtn.click();
    await page.waitForTimeout(1500);
    
    const cancelCall = network.slice(networkBefore).find(n => n.url.includes('/cancel') && n.method === 'PUT');
    if (cancelCall && cancelCall.status === 200) {
      console.log('PASS: Cancel button triggers cancel API call');
      passed++;
    } else {
      console.log('FAIL: Cancel button did not trigger API call');
      failed++;
    }
  } else {
    console.log('FAIL: Cancel button not found');
    failed++;
  }

  await page.close();
  await browser.close();

  console.log(`\n═══════════════════════════`);
  console.log(`${passed} PASS · ${failed} FAIL`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
