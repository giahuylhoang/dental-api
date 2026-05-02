import { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table';
import Fuse from 'fuse.js';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import InvoiceDrawer from './InvoiceDrawer';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';

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

const STATUS_BADGE_VARIANT: Record<Invoice['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'outline',
  issued: 'default',
  partial: 'secondary',
  paid: 'default',
  void: 'destructive',
};

const col = createColumnHelper<Invoice>();

const columns = [
  col.accessor('invoice_number', {
    header: 'Invoice #',
    cell: (info) => info.getValue() ?? info.row.original.id.slice(0, 8),
  }),
  col.accessor(
    (row) => row.patient_name ?? row.patient_id,
    {
      id: 'patient',
      header: 'Patient',
    },
  ),
  col.accessor('status', {
    header: 'Status',
    cell: (info) => (
      <Badge variant={STATUS_BADGE_VARIANT[info.getValue()]}>
        {info.getValue()}
      </Badge>
    ),
  }),
  col.accessor((row) => (row.total_cents != null ? row.total_cents / 100 : row.total), {
    id: 'total',
    header: 'Total',
    cell: (info) => <span className="text-right">{fmt.format(info.getValue())}</span>,
  }),
  col.accessor(
    (row) => Math.floor((Date.now() - new Date(row.created_at).getTime()) / 86_400_000),
    {
      id: 'age',
      header: 'Age',
      cell: (info) => `${info.getValue()}d`,
    },
  ),
];

export default function InvoiceList({ patientId }: { patientId?: string }) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [searchParams] = useSearchParams();
  const [drawerInvoiceId, setDrawerInvoiceId] = useState<string | null>(null);
  const statusFromUrl = searchParams.get('status') ?? '';
  const [statusFilter, setStatusFilter] = useState<string>(statusFromUrl);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [sorting, setSorting] = useState<SortingState>([]);

  const qs = new URLSearchParams();
  if (patientId) qs.set('patient_id', patientId);
  if (statusFilter) qs.set('status', statusFilter);
  const qsStr = qs.toString() ? `?${qs.toString()}` : '';

  const { data: invoices = [], isLoading } = useQuery<Invoice[]>({
    queryKey: ['invoices', clinicId, patientId, statusFilter],
    queryFn: () => fetcher<Invoice[]>(`/api/v2/billing/invoices${qsStr}`),
  });

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

  const table = useReactTable({
    data: visibleInvoices,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  return (
    <>
      <div className="mb-3 flex items-center gap-3">
        <Input
          type="search"
          placeholder="Search invoices…"
          aria-label="Search invoices"
          data-testid="invoice-search"
          className="w-48"
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
        <Button
          className="ml-auto"
          size="sm"
          onClick={() => setShowNewForm((v) => !v)}
        >
          + New Invoice
        </Button>
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
            <Button
              size="sm"
              disabled={createInvoice.isPending || !newPatientId}
              onClick={() => createInvoice.mutate()}
            >
              {createInvoice.isPending ? 'Creating…' : 'Create'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowNewForm(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      <table className="w-full text-sm">
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id} className="border-b text-left text-zinc-500">
              {hg.headers.map((header) => (
                <th
                  key={header.id}
                  className="pb-1 cursor-pointer select-none"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {header.column.getIsSorted() === 'asc' ? ' ↑' : header.column.getIsSorted() === 'desc' ? ' ↓' : ''}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="cursor-pointer border-b border-zinc-100 hover:bg-zinc-50"
              onClick={() => setDrawerInvoiceId(row.original.id)}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="py-1 pr-2">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
          {table.getRowModel().rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="py-4 text-center text-zinc-400">
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
