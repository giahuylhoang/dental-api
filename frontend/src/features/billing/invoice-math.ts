export interface InvoiceLine {
  id: string;
  procedure_code: string;
  description: string;
  qty: number;
  unit_price: number;
}

const GST_RATE = 0.05;

export function calcTotals(lines: InvoiceLine[], gst: boolean) {
  const subtotal = lines.reduce((s, l) => s + l.qty * l.unit_price, 0);
  const gstAmt = gst ? subtotal * GST_RATE : 0;
  return { subtotal, gstAmt, total: subtotal + gstAmt };
}
