import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';

const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });

interface Invoice {
  id: string;
  patient_id: string;
  status: 'draft' | 'issued' | 'partial' | 'paid' | 'void';
  subtotal: number;
  gst: number;
  total: number;
  balance: number;
  created_at: string;
}

const STATUS_COLORS: Record<Invoice['status'], string> = {
  draft: 'bg-zinc-100 text-zinc-600',
  issued: 'bg-blue-100 text-blue-700',
  partial: 'bg-yellow-100 text-yellow-700',
  paid: 'bg-green-100 text-green-700',
  void: 'bg-red-100 text-red-600',
};

interface PaymentModalProps {
  invoiceId: string;
  onClose: () => void;
}

function PaymentModal({ invoiceId, onClose }: PaymentModalProps) {
  const qc = useQueryClient();
  const clinicId = useAuthStore((s) => s.clinicId);
  const [method, setMethod] = useState('cash');
  const [amount, setAmount] = useState('');
  const [ref, setRef] = useState('');

  const record = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/billing/invoices/${invoiceId}/payments`, {
        method: 'POST',
        body: JSON.stringify({ method, amount: parseFloat(amount), ref }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices', clinicId] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-80 rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 font-semibold">Record Payment</h3>
        <div className="space-y-3 text-sm">
          <div>
            <label className="block text-zinc-600">Method</label>
            <select
              className="mt-1 w-full rounded border px-2 py-1"
              value={method}
              onChange={(e) => setMethod(e.target.value)}
            >
              {['cash', 'card', 'cheque', 'etransfer', 'insurance'].map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-zinc-600">Amount</label>
            <input
              type="number"
              min="0"
              step="0.01"
              className="mt-1 w-full rounded border px-2 py-1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Reference</label>
            <input
              className="mt-1 w-full rounded border px-2 py-1"
              value={ref}
              onChange={(e) => setRef(e.target.value)}
            />
          </div>
          {record.error && (
            <p className="text-xs text-red-600">{(record.error as Error).message}</p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button className="rounded px-3 py-1 hover:bg-zinc-100" onClick={onClose}>
              Cancel
            </button>
            <button
              disabled={record.isPending || !amount}
              onClick={() => record.mutate()}
              className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {record.isPending ? 'Saving…' : 'Record'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function InvoiceList({ patientId }: { patientId?: string }) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [payingId, setPayingId] = useState<string | null>(null);

  const qs = patientId ? `?patient_id=${patientId}` : '';
  const { data: invoices = [], isLoading } = useQuery<Invoice[]>({
    queryKey: ['invoices', clinicId, patientId],
    queryFn: () => fetcher<Invoice[]>(`/api/v2/billing/invoices${qs}`),
  });

  const issue = useMutation({
    mutationFn: (id: string) =>
      fetcher(`/api/v2/billing/invoices/${id}/issue`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invoices', clinicId] }),
  });

  const voidInv = useMutation({
    mutationFn: (id: string) =>
      fetcher(`/api/v2/billing/invoices/${id}/void`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invoices', clinicId] }),
  });

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  return (
    <>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-zinc-500">
            <th className="pb-1">ID</th>
            <th className="pb-1">Status</th>
            <th className="pb-1 text-right">Total</th>
            <th className="pb-1 text-right">Balance</th>
            <th className="pb-1">Date</th>
            <th className="pb-1">Actions</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => (
            <tr key={inv.id} className="border-b border-zinc-100">
              <td className="py-1 pr-2 font-mono text-xs">{inv.id.slice(0, 8)}</td>
              <td className="py-1 pr-2">
                <span className={`rounded px-1.5 py-0.5 text-xs ${STATUS_COLORS[inv.status]}`}>
                  {inv.status}
                </span>
              </td>
              <td className="py-1 pr-2 text-right">{fmt.format(inv.total)}</td>
              <td className="py-1 pr-2 text-right">{fmt.format(inv.balance)}</td>
              <td className="py-1 pr-2 text-xs text-zinc-500">
                {new Date(inv.created_at).toLocaleDateString('en-CA')}
              </td>
              <td className="py-1">
                <div className="flex gap-2">
                  {inv.status === 'draft' && (
                    <button
                      className="text-xs text-blue-600 hover:underline"
                      onClick={() => issue.mutate(inv.id)}
                    >
                      Issue
                    </button>
                  )}
                  {(inv.status === 'issued' || inv.status === 'partial') && (
                    <button
                      className="text-xs text-green-600 hover:underline"
                      onClick={() => setPayingId(inv.id)}
                    >
                      Record payment
                    </button>
                  )}
                  {inv.status !== 'void' && inv.status !== 'paid' && (
                    <button
                      className="text-xs text-red-500 hover:underline"
                      onClick={() => voidInv.mutate(inv.id)}
                    >
                      Void
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
          {invoices.length === 0 && (
            <tr>
              <td colSpan={6} className="py-4 text-center text-zinc-400">
                No invoices
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {payingId && (
        <PaymentModal invoiceId={payingId} onClose={() => setPayingId(null)} />
      )}
    </>
  );
}
