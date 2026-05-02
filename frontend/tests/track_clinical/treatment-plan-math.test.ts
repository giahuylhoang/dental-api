import { describe, expect, it } from 'vitest';

const GST_RATE = 0.05;

interface PlanItem {
  fee: number;
  insurance_coverage_pct: number | null;
}

function computeTotals(items: PlanItem[]) {
  const subtotal = items.reduce((s, i) => s + i.fee, 0);
  const insuranceEst = items.reduce(
    (s, i) => s + i.fee * ((i.insurance_coverage_pct ?? 0) / 100),
    0,
  );
  const gst = subtotal * GST_RATE;
  return { subtotal, insuranceEst, gst, patientEst: subtotal + gst - insuranceEst };
}

describe('treatment-plan-math', () => {
  it('single item no insurance', () => {
    const { subtotal, insuranceEst, gst, patientEst } = computeTotals([
      { fee: 1000, insurance_coverage_pct: null },
    ]);
    expect(subtotal).toBe(1000);
    expect(insuranceEst).toBe(0);
    expect(gst).toBeCloseTo(50);
    expect(patientEst).toBeCloseTo(1050);
  });

  it('single item 50% insurance', () => {
    const { subtotal, insuranceEst, gst, patientEst } = computeTotals([
      { fee: 1000, insurance_coverage_pct: 50 },
    ]);
    expect(subtotal).toBe(1000);
    expect(insuranceEst).toBe(500);
    expect(gst).toBeCloseTo(50);
    expect(patientEst).toBeCloseTo(550);
  });

  it('multiple items mixed coverage', () => {
    const items: PlanItem[] = [
      { fee: 1500, insurance_coverage_pct: 50 },
      { fee: 500, insurance_coverage_pct: 80 },
      { fee: 200, insurance_coverage_pct: null },
    ];
    const { subtotal, insuranceEst, gst, patientEst } = computeTotals(items);
    expect(subtotal).toBe(2200);
    expect(insuranceEst).toBeCloseTo(750 + 400);
    expect(gst).toBeCloseTo(110);
    expect(patientEst).toBeCloseTo(2200 + 110 - 1150);
  });

  it('zero items', () => {
    const { subtotal, insuranceEst, gst, patientEst } = computeTotals([]);
    expect(subtotal).toBe(0);
    expect(insuranceEst).toBe(0);
    expect(gst).toBe(0);
    expect(patientEst).toBe(0);
  });

  it('100% insurance coverage', () => {
    const { patientEst, gst } = computeTotals([
      { fee: 1000, insurance_coverage_pct: 100 },
    ]);
    // Patient still pays GST
    expect(patientEst).toBeCloseTo(gst);
  });
});
