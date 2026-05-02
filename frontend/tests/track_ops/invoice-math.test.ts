import { describe, it, expect } from 'vitest';
import { calcTotals, type InvoiceLine } from '../../src/features/billing/invoice-math';
import fixtures from '../fixtures/invoices.json';

const GST_RATE = 0.05;

describe('invoice math', () => {
  for (const fix of fixtures) {
    it(`fixture ${fix.id}: subtotal/gst/total`, () => {
      const lines: InvoiceLine[] = fix.lines.map((l, i) => ({ ...l, id: String(i) }));
      const { subtotal, gstAmt, total } = calcTotals(lines, fix.gst);

      expect(subtotal).toBeCloseTo(fix.expected_subtotal, 2);
      expect(gstAmt).toBeCloseTo(fix.expected_gst, 2);
      expect(total).toBeCloseTo(fix.expected_total, 2);

      if (fix.gst) {
        expect(gstAmt).toBeCloseTo(subtotal * GST_RATE, 10);
      } else {
        expect(gstAmt).toBe(0);
      }
    });
  }

  it('empty lines produce zero totals', () => {
    const { subtotal, gstAmt, total } = calcTotals([], true);
    expect(subtotal).toBe(0);
    expect(gstAmt).toBe(0);
    expect(total).toBe(0);
  });

  it('qty multiplier is applied', () => {
    const lines: InvoiceLine[] = [
      { id: '1', procedure_code: '00120', description: 'Adj', qty: 3, unit_price: 100 },
    ];
    const { subtotal } = calcTotals(lines, false);
    expect(subtotal).toBe(300);
  });
});
