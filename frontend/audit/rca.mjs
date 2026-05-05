export function printRCA({ page, selector, network, console: consoleLogs, backend, expected }) {
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('ROOT CAUSE ANALYSIS');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`Page: ${page}`);
  console.log(`Selector: ${selector}`);
  console.log(`Expected: ${expected}`);
  console.log('\n--- Network Requests ---');
  for (const n of network.slice(-10)) {
    console.log(`  ${n.method} ${n.url} → ${n.status} [${n.requestId || 'no-id'}]`);
    if (n.backend) console.log(`    Backend: ${n.backend.duration_ms}ms, exc=${n.backend.exc_type || 'none'}`);
  }
  console.log('\n--- Console Logs ---');
  for (const c of consoleLogs.slice(-10)) {
    console.log(`  [${c.type}] ${c.text}`);
  }
  if (backend?.length) {
    console.log('\n--- Backend Logs ---');
    for (const b of backend.slice(-5)) {
      console.log(`  ${b.method} ${b.path} → ${b.status} (${b.duration_ms}ms)`);
    }
  }
  console.log('═══════════════════════════════════════════════════════════════\n');
}
