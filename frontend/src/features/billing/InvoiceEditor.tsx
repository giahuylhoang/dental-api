import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import { calcTotals, type InvoiceLine } from './invoice-math';

export type { InvoiceLine };

const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });

interface Props {
  patientId: string;
  appointmentId?: string;
  onSaved?: (invoiceId: string) => void;
}

export default function InvoiceEditor({ patientId, appointmentId, onSaved }: Props) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [lines, setLines] = useState<InvoiceLine[]>([
    { id: '1', procedure_code: '', description: '', qty: 1, unit_price: 0 },
  ]);
  const [gst, setGst] = useState(true);

  const { subtotal, gstAmt, total } = calcTotals(lines, gst);

  const save = useMutation({
    mutationFn: () =>
      fetcher<{ id: string }>('/api/v2/billing/invoices', {
        method: 'POST',
        body: JSON.stringify({
          patient_id: patientId,
          appointment_id: appointmentId,
          lines: lines.map(({ procedure_code, description, qty, unit_price }) => ({
            procedure_code,
            description,
            qty,
            unit_price,
          })),
          gst,
        }),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['invoices', clinicId, patientId] });
      onSaved?.(data.id);
    },
  });

  function updateLine(id: string, field: keyof InvoiceLine, value: string | number) {
    setLines((ls) => ls.map((l) => (l.id === id ? { ...l, [field]: value } : l)));
  }

  function addLine() {
    setLines((ls) => [
      ...ls,
      { id: String(Date.now()), procedure_code: '', description: '', qty: 1, unit_price: 0 },
    ]);
  }

  function removeLine(id: string) {
    setLines((ls) => ls.filter((l) => l.id !== id));
  }

  return (
    <div className="space-y-4">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-zinc-500">
            <th className="pb-1">Code</th>
            <th className="pb-1">Description</th>
            <th className="pb-1 text-right">Qty</th>
            <th className="pb-1 text-right">Unit Price</th>
            <th className="pb-1 text-right">Total</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {lines.map((l) => (
            <tr key={l.id} className="border-b border-zinc-100">
              <td className="py-1 pr-2">
                <input
                  className="w-24 rounded border px-1"
                  value={l.procedure_code}
                  onChange={(e) => updateLine(l.id, 'procedure_code', e.target.value)}
                  placeholder="e.g. 31310"
                />
              </td>
              <td className="py-1 pr-2">
                <input
                  className="w-full rounded border px-1"
                  value={l.description}
                  onChange={(e) => updateLine(l.id, 'description', e.target.value)}
                />
              </td>
              <td className="py-1 pr-2 text-right">
                <input
                  type="number"
                  min="1"
                  className="w-14 rounded border px-1 text-right"
                  value={l.qty}
                  onChange={(e) => updateLine(l.id, 'qty', parseInt(e.target.value) || 1)}
                />
              </td>
              <td className="py-1 pr-2 text-right">
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  className="w-24 rounded border px-1 text-right"
                  value={l.unit_price}
                  onChange={(e) => updateLine(l.id, 'unit_price', parseFloat(e.target.value) || 0)}
                />
              </td>
              <td className="py-1 pr-2 text-right">{fmt.format(l.qty * l.unit_price)}</td>
              <td className="py-1">
                <button
                  className="text-xs text-red-500 hover:underline"
                  onClick={() => removeLine(l.id)}
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <button className="text-sm text-blue-600 hover:underline" onClick={addLine}>
        + Add line
      </button>

      <div className="flex items-center gap-2 text-sm">
        <input
          id="gst-toggle"
          type="checkbox"
          checked={gst}
          onChange={(e) => setGst(e.target.checked)}
        />
        <label htmlFor="gst-toggle">Apply GST (5%)</label>
      </div>

      <div className="space-y-1 text-right text-sm">
        <div>Subtotal: {fmt.format(subtotal)}</div>
        {gst && <div>GST (5%): {fmt.format(gstAmt)}</div>}
        <div className="font-semibold">Total: {fmt.format(total)}</div>
      </div>

      {save.error && (
        <p className="text-xs text-red-600">{(save.error as Error).message}</p>
      )}

      <button
        disabled={save.isPending}
        onClick={() => save.mutate()}
        className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {save.isPending ? 'Saving…' : 'Save Invoice'}
      </button>
    </div>
  );
}
