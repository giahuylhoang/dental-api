import { http, HttpResponse } from 'msw';

// ── Scheduling ──────────────────────────────────────────────────────────────
export const schedulingHandlers = [
  http.get('/api/v2/scheduling/appointments', () => HttpResponse.json([])),
  http.post('/api/v2/scheduling/appointments', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 'appt-new', ...(body as object) }, { status: 201 });
  }),
  http.get('/api/v2/scheduling/waitlist', () => HttpResponse.json([])),
  http.post('/api/v2/scheduling/waitlist/:id/fill', ({ params }) =>
    HttpResponse.json({ id: params.id, status: 'filled' }),
  ),
];

// ── Billing ──────────────────────────────────────────────────────────────────
const invoicesDb: Record<string, unknown>[] = [];

export const billingHandlers = [
  http.get('/api/v2/billing/invoices', () => HttpResponse.json(invoicesDb)),
  http.post('/api/v2/billing/invoices', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    const inv = { id: `inv-${Date.now()}`, status: 'draft', balance: 0, created_at: new Date().toISOString(), ...body };
    invoicesDb.push(inv);
    return HttpResponse.json(inv, { status: 201 });
  }),
  http.post('/api/v2/billing/invoices/:id/issue', ({ params }) =>
    HttpResponse.json({ id: params.id, status: 'issued' }),
  ),
  http.post('/api/v2/billing/invoices/:id/void', ({ params }) =>
    HttpResponse.json({ id: params.id, status: 'void' }),
  ),
  http.post('/api/v2/billing/invoices/:id/payments', async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: `pay-${Date.now()}`, invoice_id: params.id, ...(body as object) }, { status: 201 });
  }),
];

// ── Communications ────────────────────────────────────────────────────────────
const commsDb: Record<string, unknown>[] = [];

export const communicationsHandlers = [
  http.get('/api/v2/communications', () => HttpResponse.json(commsDb)),
  http.post('/api/v2/communications/send', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    const msg = {
      id: `msg-${Date.now()}`,
      direction: 'outbound',
      status: 'sent',
      created_at: new Date().toISOString(),
      ...body,
    };
    commsDb.push(msg);
    return HttpResponse.json(msg, { status: 201 });
  }),
];

// ── CRM ───────────────────────────────────────────────────────────────────────
export const crmHandlers = [
  http.post('/api/v2/crm/leads/:id/convert', ({ params }) =>
    HttpResponse.json({ patient_id: `patient-from-${params.id}` }, { status: 201 }),
  ),
  http.get('/api/v2/crm/leads/:id/events', () => HttpResponse.json([])),
];

// ── Reporting ─────────────────────────────────────────────────────────────────
export const reportingHandlers = [
  http.get('/api/v2/reporting/kpi', () =>
    HttpResponse.json({
      production_this_month: 0,
      ar_aging: [
        { bucket: '0–30', amount: 0 },
        { bucket: '31–60', amount: 0 },
        { bucket: '61–90', amount: 0 },
        { bucket: '90+', amount: 0 },
      ],
      no_show_rate: 0,
      lab_cost_per_case: 0,
    }),
  ),
  http.get('/api/v2/reporting/production-by-provider', () => HttpResponse.json([])),
  http.get('/api/v2/reporting/remake-rate-by-lab', () => HttpResponse.json([])),
];
