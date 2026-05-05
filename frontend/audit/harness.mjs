import { chromium } from '@playwright/test';
import { readFileSync } from 'fs';

const BRAVE_PATH = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser';

export async function launchBrave() {
  const executablePath = process.env.BRAVE_PATH === 'skip' ? undefined : BRAVE_PATH;
  return chromium.launch({ executablePath, headless: true });
}

export function recordPage(page) {
  const network = [];
  const console_ = [];

  page.on('console', msg => console_.push({ ts: Date.now(), type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => console_.push({ ts: Date.now(), type: 'error', text: err.message }));
  page.on('requestfinished', async req => {
    const res = await req.response();
    network.push({
      ts: Date.now(),
      method: req.method(),
      url: req.url(),
      status: res?.status(),
      requestId: res?.headers()['x-request-id']
    });
  });
  page.on('requestfailed', req => {
    network.push({ ts: Date.now(), method: req.method(), url: req.url(), status: 0, error: req.failure()?.errorText });
  });

  return { network, console: console_ };
}

export function joinBackendLog(network, logPath = '/tmp/dental-logs/backend.log') {
  let lines = [];
  try { lines = readFileSync(logPath, 'utf8').split('\n').filter(Boolean); } catch { return []; }
  
  const byReqId = new Map();
  for (const line of lines) {
    try {
      const obj = JSON.parse(line);
      if (obj.request_id) byReqId.set(obj.request_id, obj);
    } catch {}
  }

  return network.map(n => ({ ...n, backend: byReqId.get(n.requestId) || null }));
}
