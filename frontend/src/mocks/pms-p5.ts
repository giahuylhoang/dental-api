import { http, HttpResponse } from 'msw';

interface Claim {
  id: string;
  invoice_id: string;
  carrier: string;
  kind: string;
  status: 'draft' | 'submitted' | 'adjudicated' | 'paid';
  response_codes: string[];
  outcome?: string;
  accepted_amount_cents?: number;
  notes?: string;
  created_at: string;
}

const claimsDb: Record<string, Claim> = {};
let claimCounter = 1;

// Extend invoicesDb with detail fields
const invoiceDetailDb: Record<string, { payments: unknown[]; claims: string[] }> = {};

function getInvoiceDetail(id: string) {
  if (!invoiceDetailDb[id]) {
    invoiceDetailDb[id] = { payments: [], claims: [] };
  }
  return invoiceDetailDb[id];
}

export const pmsP5Handlers = [
  // GET single invoice (detail)
  http.get('/api/v2/billing/invoices/:id', ({ params }) => {
    const id = params.id as string;
    const detail = getInvoiceDetail(id);
    const claimObjs = detail.claims
      .map((cid) => claimsDb[cid])
      .filter(Boolean);
    return HttpResponse.json({
      id,
      patient_id: 'p1',
      status: 'issued',
      subtotal: 100,
      gst: 5,
      total: 105,
      balance: 105,
      lines: [
        { id: 'l1', description: 'Cleaning', qty: 1, unit_price_cents: 10000 },
      ],
      payments: detail.payments,
      claims: claimObjs,
      created_at: new Date().toISOString(),
    });
  }),

  // POST payment — update detail
  http.post('/api/v2/billing/invoices/:id/payments', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as Record<string, unknown>;
    const payment = { id: `pay-${Date.now()}`, invoice_id: id, ...body, created_at: new Date().toISOString() };
    getInvoiceDetail(id).payments.push(payment);
    return HttpResponse.json(payment, { status: 201 });
  }),

  // Insurance claims
  http.post('/api/v2/insurance/claims', async ({ request }) => {
    const body = (await request.json()) as { invoice_id: string; carrier: string; kind: string };
    const claim: Claim = {
      id: `claim-${claimCounter++}`,
      invoice_id: body.invoice_id,
      carrier: body.carrier,
      kind: body.kind,
      status: 'draft',
      response_codes: [],
      created_at: new Date().toISOString(),
    };
    claimsDb[claim.id] = claim;
    getInvoiceDetail(body.invoice_id).claims.push(claim.id);
    return HttpResponse.json(claim, { status: 201 });
  }),

  http.get('/api/v2/insurance/claims/:id', ({ params }) => {
    const claim = claimsDb[params.id as string];
    if (!claim) {
      // Return a default claim for tests that open a claim by id directly
      return HttpResponse.json({
        id: params.id,
        invoice_id: 'inv-test',
        carrier: 'Sun Life',
        kind: 'claim',
        status: 'submitted',
        response_codes: [],
        created_at: new Date().toISOString(),
      });
    }
    return HttpResponse.json(claim);
  }),

  http.post('/api/v2/insurance/claims/:id/submit', ({ params }) => {
    const id = params.id as string;
    if (claimsDb[id]) claimsDb[id].status = 'submitted';
    return HttpResponse.json({ ...(claimsDb[id] ?? { id, status: 'submitted' }) });
  }),

  http.post('/api/v2/insurance/claims/:id/adjudicate', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as {
      outcome: string;
      accepted_amount_cents?: number;
      notes?: string;
    };
    if (claimsDb[id]) {
      claimsDb[id].status = 'adjudicated';
      claimsDb[id].outcome = body.outcome;
      claimsDb[id].accepted_amount_cents = body.accepted_amount_cents;
      claimsDb[id].notes = body.notes;
    }
    return HttpResponse.json({ ...(claimsDb[id] ?? { id, status: 'adjudicated', ...body }) });
  }),

  http.post('/api/v2/insurance/claims/:id/mark-paid', ({ params }) => {
    const id = params.id as string;
    if (claimsDb[id]) claimsDb[id].status = 'paid';
    return HttpResponse.json({ ...(claimsDb[id] ?? { id, status: 'paid' }) });
  }),
];
