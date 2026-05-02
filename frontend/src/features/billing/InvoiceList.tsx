import { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import Fuse from 'fuse.js';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import InvoiceDrawer from './InvoiceDrawer';

const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });

interface Invoice {
  id: string;
  invoice_number?: string;
  patient_id: string;
  patient_name?: string;
  status: 'draft' | 'issued' | 'partial' | 'paid' | 'void';
  subtotal: number;
  gst: number;
  total: number;
  total_cents?: number;
  balance: number;
  created_at: string;
}

interface DentureCase {
  id: string;
  arch: string;
  case_type: string;
}

const STATUS_COLORS: Record<Invoice['status'], string> = {
  draft: 'bg-zinc-100 text-zinc-600',
  issued: 'bg-blue-100 text-blue-700',
  partial: 'bg-yellow-100 text-yellow-700',
  paid: 'bg-green-100 text-green-700',
  void: 'bg-red-100 text-red-600',
};

export default function InvoiceList({ patientId }: { patientId?: string }) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [searchParams] = useSearchParams();
  const [drawerInvoiceId, setDrawerInvoiceId] = useState<string | null>(null);
  const statusFromUrl = searchParams.get('status') ?? '';
  const [statusFilter, setStatusFilter] = useState<string>(statusFromUrl);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  const qs = new URLSearchParams();
  if (patientId) qs.set('patient_id', patientId);
  if (statusFilter) qs.set('status', statusFilter);
  const qsStr = qs.toString() ? `?${qs.toString()}` : '';

  const { data: invoices = [], isLoading } = useQuery<Invoice[]>({
    queryKey: ['invoices', clinicId, patientId, statusFilter],
    queryFn: () => fetcher<Invoice[]>(`/api/v2/billing/invoices${qsStr}`),
  });

  // Debounce search query 200ms
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(searchQuery), 200);
    return () => clearTimeout(t);
  }, [searchQuery]);

  const fuse = useMemo(
    () =>
      new Fuse(invoices, {
        keys: ['invoice_number', 'patient_name', 'status'],
        threshold: 0.2,
        ignoreLocation: true,
      }),
    [invoices],
  );

  const visibleInvoices = debouncedQuery
    ? fuse.search(debouncedQuery).map((r) => r.item)
    : invoices;

  const { data: dentureCases = [] } = useQuery<DentureCase[]>({
    queryKey: ['denture-cases', patientId],
    queryFn: () => fetcher<DentureCase[]>(`/api/v2/clinical/patients/${patientId}/denture-cases`),
    enabled: !!patientId,
  });

  // New invoice form state
  const [showNewForm, setShowNewForm] = useState(false);
  const [newPatientId, setNewPatientId] = useState(patientId ?? '');
  const [newDentureCaseId, setNewDentureCaseId] = useState('');

  const createInvoice = useMutation({
    mutationFn: () =>
      fetcher('/api/v2/billing/invoices', {
        method: 'POST',
        body: JSON.stringify({
          patient_id: newPatientId,
          denture_case_id: newDentureCaseId || undefined,
          lines: [],
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices', clinicId] });
      setShowNewForm(false);
      setNewDentureCaseId('');
    },
  });

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  return (
    <>
      <div className="mb-3 flex items-center gap-3">
        <input
          type="search"
          placeholder="Search invoices…"
          aria-label="Search invoices"
          className="rounded border border-zinc-300 px-2 py-1 text-sm"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <select
          className="rounded border border-zinc-300 px-2 py-1 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All statuses</option>
          {(['draft', 'issued', 'partial', 'paid', 'void', 'overdue'] as const).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button
          className="ml-auto rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
          onClick={() => setShowNewForm((v) => !v)}
        >
          + New Invoice
        </button>
      </div>

      {showNewForm && (
        <div className="mb-4 space-y-2 rounded border border-zinc-200 p-3 text-sm">
          {!patientId && (
            <div>
              <label className="block text-zinc-600">Patient ID</label>
              <input
                className="mt-1 w-full rounded border px-2 py-1"
                value={newPatientId}
                onChange={(e) => setNewPatientId(e.target.value)}
              />
            </div>
          )}
          {dentureCases.length > 0 && (
            <div>
              <label className="block text-zinc-600">Denture Case (optional)</label>
              <select
                className="mt-1 w-full rounded border px-2 py-1"
                value={newDentureCaseId}
                onChange={(e) => setNewDentureCaseId(e.target.value)}
              >
                <option value="">None</option>
                {dentureCases.map((dc) => (
                  <option key={dc.id} value={dc.id}>
                    {dc.arch} · {dc.case_type} ({dc.id.slice(0, 8)})
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="flex gap-2">
            <button
              disabled={createInvoice.isPending || !newPatientId}
              onClick={() => createInvoice.mutate()}
              className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createInvoice.isPending ? 'Creating…' : 'Create'}
            </button>
            <button
              className="rounded border border-zinc-300 px-3 py-1 text-sm hover:bg-zinc-50"
              onClick={() => setShowNewForm(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-zinc-500">
            <th className="pb-1">ID</th>
            <th className="pb-1">Patient</th>
            <th className="pb-1">Status</th>
            <th className="pb-1 text-right">Total</th>
            <th className="pb-1 text-right">Balance</th>
            <th className="pb-1">Date</th>
          </tr>
        </thead>
        <tbody>
          {visibleInvoices.map((inv) => (
            <tr
              key={inv.id}
              className="cursor-pointer border-b border-zinc-100 hover:bg-zinc-50"
              onClick={() => setDrawerInvoiceId(inv.id)}
            >
              <td className="py-1 pr-2 font-mono text-xs">{inv.id.slice(0, 8)}</td>
              <td className="py-1 pr-2 text-sm">{inv.patient_name ?? inv.patient_id.slice(0, 8)}</td>
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
            </tr>
          ))}
          {visibleInvoices.length === 0 && (
            <tr>
              <td colSpan={6} className="py-4 text-center text-zinc-400">
                No invoices
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <InvoiceDrawer
        invoiceId={drawerInvoiceId}
        open={!!drawerInvoiceId}
        onClose={() => setDrawerInvoiceId(null)}
        onChanged={() => qc.invalidateQueries({ queryKey: ['invoices', clinicId] })}
      />
    </>
  );
}
