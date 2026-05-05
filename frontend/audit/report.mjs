#!/usr/bin/env node
/**
 * Observability report generator.
 * Reads audit output files and generates REPORT.md with:
 * - Dead-button trend over time
 * - Top 10 latencies
 * - Top 10 exceptions by exc_type
 */

import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

const AUDIT_OUT = 'audit/out';

function readJsonSafe(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf-8'));
  } catch {
    return null;
  }
}

function generateReport() {
  const lines = [];
  lines.push('# Audit Report');
  lines.push(`Generated: ${new Date().toISOString()}`);
  lines.push('');

  // Dead buttons
  const deadButtons = readJsonSafe(join(AUDIT_OUT, 'dead-buttons.json'));
  if (deadButtons) {
    lines.push('## Dead Buttons');
    lines.push(`Total: ${deadButtons.length}`);
    lines.push('');
    
    // Group by page
    const byPage = {};
    for (const btn of deadButtons) {
      byPage[btn.page] = (byPage[btn.page] || 0) + 1;
    }
    lines.push('| Page | Count |');
    lines.push('|------|-------|');
    for (const [page, count] of Object.entries(byPage).sort((a, b) => b[1] - a[1])) {
      lines.push(`| ${page} | ${count} |`);
    }
    lines.push('');
  }

  // Network logs (if any)
  const networkFiles = [];
  try {
    const dirs = readdirSync(AUDIT_OUT, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);
    for (const dir of dirs) {
      const networkPath = join(AUDIT_OUT, dir, 'network.json');
      if (existsSync(networkPath)) {
        const data = readJsonSafe(networkPath);
        if (data) networkFiles.push(...data);
      }
    }
  } catch {}

  if (networkFiles.length > 0) {
    lines.push('## Top 10 Latencies');
    const sorted = networkFiles
      .filter(n => n.durationMs)
      .sort((a, b) => (b.durationMs || 0) - (a.durationMs || 0))
      .slice(0, 10);
    
    lines.push('| Path | Duration (ms) |');
    lines.push('|------|---------------|');
    for (const n of sorted) {
      lines.push(`| ${n.path || n.url || 'unknown'} | ${n.durationMs} |`);
    }
    lines.push('');
  }

  // Console errors (if any)
  const consoleErrors = [];
  try {
    const dirs = readdirSync(AUDIT_OUT, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);
    for (const dir of dirs) {
      const consolePath = join(AUDIT_OUT, dir, 'console.json');
      if (existsSync(consolePath)) {
        const data = readJsonSafe(consolePath);
        if (data) consoleErrors.push(...data.filter(c => c.type === 'error'));
      }
    }
  } catch {}

  if (consoleErrors.length > 0) {
    lines.push('## Top 10 Exceptions');
    const byType = {};
    for (const err of consoleErrors) {
      const type = err.text?.split(':')[0] || 'Unknown';
      byType[type] = (byType[type] || 0) + 1;
    }
    
    lines.push('| Exception Type | Count |');
    lines.push('|----------------|-------|');
    for (const [type, count] of Object.entries(byType).sort((a, b) => b[1] - a[1]).slice(0, 10)) {
      lines.push(`| ${type} | ${count} |`);
    }
    lines.push('');
  }

  // Summary
  lines.push('## Summary');
  lines.push(`- Dead buttons: ${deadButtons?.length || 0}`);
  lines.push(`- Network requests logged: ${networkFiles.length}`);
  lines.push(`- Console errors: ${consoleErrors.length}`);
  lines.push('');

  mkdirSync(AUDIT_OUT, { recursive: true });
  writeFileSync(join(AUDIT_OUT, 'REPORT.md'), lines.join('\n'));
  console.log(`Report generated: ${join(AUDIT_OUT, 'REPORT.md')}`);
}

const start = Date.now();
generateReport();
console.log(`Completed in ${Date.now() - start}ms`);
