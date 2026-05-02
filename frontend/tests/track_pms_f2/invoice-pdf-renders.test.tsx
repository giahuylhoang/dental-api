import { describe, it, expect } from 'vitest';
import { pdf } from '@react-pdf/renderer';
import InvoicePdf from '../../src/features/billing/InvoicePdf';

const fixture = {
  id: 'inv-pdf-1',
  invoice_number: 'INV-PDF-001',
  patient_id: 'p1',
  patient_name: 'Test Patient',
  status: 'issued' as const,
  subtotal: 100,
  gst: 5,
  total: 105,
  total_cents: 10500,
  balance: 105,
  lines: [
    { id: 'l1', description: 'Cleaning', qty: 1, unit_price_cents: 10000 },
  ],
  created_at: '2024-01-01T00:00:00Z',
};

describe('InvoicePdf renders to PDF blob', () => {
  it('produces a non-empty PDF blob', async () => {
    const blob = await pdf(<InvoicePdf invoice={fixture} />).toBlob();
    expect(blob.size).toBeGreaterThan(0);
    expect(blob.type).toBe('application/pdf');
  }, 15000);
});
