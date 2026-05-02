import { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { type ColumnDef } from '@tanstack/react-table';
import Fuse from 'fuse.js';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import InvoiceDrawer from './InvoiceDrawer';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card } from '../../components/ui/card';
import { PageHeader } from '../../components/ui/page-header';
import { DataTable } from '../../components/ui/data-table';

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

const STATUS_BADGE_VARIANT: Record<Invoice['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'outline',
  issued: 'default',
  partial: 'secondary',
  paid: 'default',
  void: 'destructive',
};

const columns: ColumnDef<Invoice>[] = [
  {
    accessorKey: 'invoice_number',
    header: 'Invoice #',
    cell: ({ row }) => row.original.invoice_number ?? row.original.id.slice(0, 8),
  },
  {
    id: 'patient',
    header: 'Patient',
    accessorFn: (row) => row.patient_name ?? row.patient_id,
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => (
      <Badge variant={STATUS_BADGE_VARIANT[row.original.status]}>
        {row.original.status}
      </Badge>
    ),
  },
  {
    id: 'total',
    header: 'Total',
    accessorFn: (row) => (row.total_cents != null ? row.total_cents / 100 : row.total),
    cell: ({ getValue }) => fmt.format(getValue() as number),
  },
  {
    id: 'age',
    header: 'Age',
    accessorFn: (row) => Math.floor((Date.now() - new Date(row.created_at).getTime()) / 86_400_000),
    cell: ({ getValue }) => `${getValue()}d`,
  },
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

  const outstanding = invoices.filter((i) => i.status === 'issued' || i.status === 'partial');
  const outstandingTotal = outstanding.reduce((sum, i) => sum + (i.total_cents != null ? i.total_cents / 100 : i.total), 0);

  const createInvoice = useMutation({
    mutationFn: () =>
      fetcher('/api/v2/billing/invoices', {
        method: 'POST',
        body: JSON.stringify({ patient_id: patientId ?? '', lines: [] }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices', clinicId] });
    },
  });

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  return (
    <>
      <PageHeader
        title="Billing"
        description={`${fmt.format(outstandingTotal)} outstanding`}
        actions={
          <Button onClick={() => createInvoice.mutate()} disabled={createInvoice.isPending}>
            + New invoice
          </Button>
        }
      />

      <Card className="mb-4 p-3">
        <div className="flex flex-wrap items-center gap-3">
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
            className="rounded border border-zinc-300 px-2 py-1.5 text-sm"
            value={statusFilter || 'all'}
            onChange={(e) => setStatusFilter(e.target.value === 'all' ? '' : e.target.value)}
          >
            <option value="all">All statuses</option>
            {(['draft', 'issued', 'partial', 'paid', 'void', 'overdue'] as const).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <div className="ml-auto text-xs text-zinc-400">Date range placeholder</div>
        </div>
      </Card>

      <div data-testid="invoice-data-table">
        <DataTable
          columns={columns}
          data={visibleInvoices}
          onRowClick={(row) => setDrawerInvoiceId(row.id)}
        />
      </div>

      <InvoiceDrawer
        invoiceId={drawerInvoiceId}
        open={!!drawerInvoiceId}
        onClose={() => setDrawerInvoiceId(null)}
        onChanged={() => qc.invalidateQueries({ queryKey: ['invoices', clinicId] })}
      />
    </>
  );
}
