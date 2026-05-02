import { http, HttpResponse } from 'msw';

function makeInvoice(i: number) {
  const statuses = ['draft', 'issued', 'partial', 'paid', 'void'] as const;
  const cents = (i + 1) * 5000;
  return {
    id: `inv-f2-${i}`,
    invoice_number: `INV-F2-${String(i).padStart(3, '0')}`,
    patient_id: `patient-${i}`,
    patient_name: `Patient ${i}`,
    status: statuses[i % statuses.length],
    subtotal: cents / 100,
    gst: (cents * 0.05) / 100,
    total: (cents * 1.05) / 100,
    total_cents: Math.round(cents * 1.05),
    balance: (cents * 1.05) / 100,
    created_at: new Date(Date.now() - i * 86_400_000).toISOString(),
  };
}

export const seedInvoices = Array.from({ length: 12 }, (_, i) => makeInvoice(i));

export const pmsF2Handlers = [
  http.get('/api/v2/billing/invoices', () => HttpResponse.json(seedInvoices)),
];
