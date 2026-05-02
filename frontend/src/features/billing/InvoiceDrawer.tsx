import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pdf } from '@react-pdf/renderer';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '../../components/ui/sheet';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import FormField from '../../components/forms/FormField';
import SubmitClaimForm from './SubmitClaimForm';
import ClaimDrawer from './ClaimDrawer';
import InvoicePdf from './InvoicePdf';

const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });

interface InvoiceLine {
  id: string;
  description: string;
  qty: number;
  unit_price_cents: number;
}

interface Payment {
  id: string;
  method: string;
  amount: number;
  ref?: string;
  created_at: string;
}

interface Claim {
  id: string;
  carrier: string;
  kind: string;
  status: string;
}

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
  lines?: InvoiceLine[];
  payments?: Payment[];
  claims?: Claim[];
  created_at: string;
}

interface Props {
  invoiceId?: string | null;
  invoice?: Invoice;
  open?: boolean;
  onClose: () => void;
  onChanged?: () => void;
}

const STATUS_BADGE_VARIANT: Record<Invoice['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'outline',
  issued: 'default',
  partial: 'secondary',
  paid: 'default',
  void: 'destructive',
};

function RecordPaymentForm({ invoiceId, onClose }: { invoiceId: string; onClose: () => void }) {
  const qc = useQueryClient();
  const clinicId = useAuthStore((s) => s.clinicId);
  const [method, setMethod] = useState('cash');
  const [amount, setAmount] = useState('');
  const [ref, setRef] = useState('');

  const record = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/billing/invoices/${invoiceId}/payments`, {
        method: 'POST',
        body: JSON.stringify({ method, amount: parseFloat(amount), ref: ref || undefined }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoice', invoiceId] });
      qc.invalidateQueries({ queryKey: ['invoices', clinicId] });
      onClose();
    },
  });

  return (
    <div className="space-y-3 rounded border border-zinc-200 p-3">
      <h4 className="text-sm font-semibold">Record Payment</h4>
      <FormField label="Method" name="method">
        <select
          id="method"
          className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
          value={method}
          onChange={(e) => setMethod(e.target.value)}
        >
          {['cash', 'card', 'cheque', 'etransfer', 'insurance'].map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </FormField>
      <FormField label="Amount ($)" name="amount">
        <input
          id="amount"
          type="number"
          min="0"
          step="0.01"
          className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </FormField>
      <FormField label="Reference" name="ref">
        <input
          id="ref"
          className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
          value={ref}
          onChange={(e) => setRef(e.target.value)}
        />
      </FormField>
      {record.error && (
        <p className="text-xs text-red-600">{(record.error as Error).message}</p>
      )}
      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={record.isPending || !amount}
          onClick={() => record.mutate()}
        >
          {record.isPending ? 'Saving…' : 'Record'}
        </Button>
        <Button variant="outline" size="sm" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

export default function InvoiceDrawer({ invoiceId, invoice: invoiceProp, open = true, onClose, onChanged }: Props) {
  const qc = useQueryClient();
  const clinicId = useAuthStore((s) => s.clinicId);
  const [showPayment, setShowPayment] = useState(false);
  const [showClaim, setShowClaim] = useState(false);
  const [openClaimId, setOpenClaimId] = useState<string | null>(null);

  const resolvedId = invoiceProp?.id ?? invoiceId ?? null;

  const { data: fetchedInvoice, isLoading } = useQuery<Invoice>({
    queryKey: ['invoice', resolvedId],
    queryFn: () => fetcher<Invoice>(`/api/v2/billing/invoices/${resolvedId}`),
    enabled: !!resolvedId && open && !invoiceProp,
  });

  const invoice = invoiceProp ?? fetchedInvoice;

  async function handleDownloadPdf() {
    if (!invoice) return;
    const blob = await pdf(<InvoicePdf invoice={invoice} />).toBlob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `invoice-${invoice.invoice_number ?? invoice.id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const issue = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/billing/invoices/${resolvedId}/issue`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoice', resolvedId] });
      qc.invalidateQueries({ queryKey: ['invoices', clinicId] });
      onChanged?.();
    },
  });

  const voidInv = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/billing/invoices/${resolvedId}/void`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoice', resolvedId] });
      qc.invalidateQueries({ queryKey: ['invoices', clinicId] });
      onChanged?.();
      onClose();
    },
  });

  return (
    <>
      <Sheet open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
        <SheetContent side="right" className="w-[480px] sm:max-w-[480px] overflow-y-auto">
          <SheetHeader className="mb-4">
            <div className="flex items-center gap-3">
              <SheetTitle className="font-mono text-sm">
                {invoice?.invoice_number ?? resolvedId?.slice(0, 8) ?? ''}
              </SheetTitle>
              {invoice && (
                <Badge variant={STATUS_BADGE_VARIANT[invoice.status]}>
                  {invoice.status}
                </Badge>
              )}
            </div>
            {invoice?.patient_name && (
              <p className="text-sm text-zinc-500">{invoice.patient_name}</p>
            )}
          </SheetHeader>

          {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}

          {invoice && (
            <Tabs defaultValue="detail">
              <TabsList className="mb-4 w-full">
                <TabsTrigger value="detail" className="flex-1">Detail</TabsTrigger>
                <TabsTrigger value="lines" className="flex-1">Lines</TabsTrigger>
                <TabsTrigger value="payments" className="flex-1">Payments</TabsTrigger>
                <TabsTrigger value="claims" className="flex-1">Claims</TabsTrigger>
                <TabsTrigger value="pdf" className="flex-1">PDF</TabsTrigger>
              </TabsList>

              <TabsContent value="detail">
                <div className="space-y-4">
                  <div className="space-y-1 rounded bg-zinc-50 p-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Subtotal</span>
                      <span>{fmt.format(invoice.subtotal)}</span>
                    </div>
                    {invoice.gst > 0 && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">GST</span>
                        <span>{fmt.format(invoice.gst)}</span>
                      </div>
                    )}
                    <div className="flex justify-between font-semibold">
                      <span>Total</span>
                      <span>{fmt.format(invoice.total)}</span>
                    </div>
                    <div className="flex justify-between text-blue-700">
                      <span>Balance</span>
                      <span>{fmt.format(invoice.balance)}</span>
                    </div>
                  </div>
                  <div className="text-xs text-zinc-500">
                    Date: {new Date(invoice.created_at).toLocaleDateString('en-CA')}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {invoice.status === 'draft' && (
                      <Button size="sm" disabled={issue.isPending} onClick={() => issue.mutate()}>
                        {issue.isPending ? 'Issuing…' : 'Issue'}
                      </Button>
                    )}
                    {(invoice.status === 'issued' || invoice.status === 'partial') && (
                      <Button size="sm" variant="outline" onClick={() => { setShowPayment(true); setShowClaim(false); }}>
                        Record Payment
                      </Button>
                    )}
                    {invoice.status !== 'void' && invoice.status !== 'paid' && (
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={voidInv.isPending}
                        onClick={() => { if (confirm('Void this invoice?')) voidInv.mutate(); }}
                      >
                        Void
                      </Button>
                    )}
                    <Button size="sm" variant="outline" onClick={handleDownloadPdf}>
                      Download PDF
                    </Button>
                  </div>
                  {showPayment && (
                    <RecordPaymentForm invoiceId={invoice.id} onClose={() => setShowPayment(false)} />
                  )}
                  {showClaim && (
                    <SubmitClaimForm
                      invoiceId={invoice.id}
                      patientId={invoice.patient_id}
                      onSuccess={(claimId) => { setShowClaim(false); setOpenClaimId(claimId); onChanged?.(); }}
                      onCancel={() => setShowClaim(false)}
                    />
                  )}
                </div>
              </TabsContent>

              <TabsContent value="lines">
                {invoice.lines && invoice.lines.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-zinc-500">
                        <th className="pb-1">Description</th>
                        <th className="pb-1 text-right">Qty</th>
                        <th className="pb-1 text-right">Unit</th>
                        <th className="pb-1 text-right">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invoice.lines.map((line) => (
                        <tr key={line.id} className="border-b border-zinc-100">
                          <td className="py-1 pr-2">{line.description}</td>
                          <td className="py-1 pr-2 text-right">{line.qty}</td>
                          <td className="py-1 pr-2 text-right">${(line.unit_price_cents / 100).toFixed(2)}</td>
                          <td className="py-1 text-right">${((line.qty * line.unit_price_cents) / 100).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-sm text-zinc-400">No line items.</p>
                )}
              </TabsContent>

              <TabsContent value="payments">
                {invoice.payments && invoice.payments.length > 0 ? (
                  <ul className="space-y-1">
                    {invoice.payments.map((p) => (
                      <li key={p.id} className="flex justify-between rounded bg-zinc-50 px-2 py-1 text-sm">
                        <span className="capitalize text-zinc-600">{p.method}{p.ref ? ` · ${p.ref}` : ''}</span>
                        <span>{fmt.format(p.amount)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-zinc-400">No payments recorded.</p>
                )}
              </TabsContent>

              <TabsContent value="claims">
                <div className="space-y-2">
                  {invoice.claims && invoice.claims.length > 0 ? (
                    <ul className="space-y-1">
                      {invoice.claims.map((c) => (
                        <li key={c.id} className="flex items-center justify-between rounded bg-zinc-50 px-2 py-1 text-sm">
                          <span>{c.carrier} · {c.kind} · <span className="text-zinc-500">{c.status}</span></span>
                          <Button variant="ghost" size="sm" onClick={() => setOpenClaimId(c.id)}>View</Button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-zinc-400">No claims.</p>
                  )}
                  {invoice.status !== 'void' && (
                    <Button size="sm" variant="outline" onClick={() => { setShowClaim(true); setShowPayment(false); }}>
                      Submit Claim
                    </Button>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="pdf">
                <Button size="sm" variant="outline" onClick={handleDownloadPdf}>
                  Download PDF
                </Button>
              </TabsContent>
            </Tabs>
          )}
        </SheetContent>
      </Sheet>

      <ClaimDrawer
        claimId={openClaimId}
        open={!!openClaimId}
        onClose={() => setOpenClaimId(null)}
        onChanged={() => {
          qc.invalidateQueries({ queryKey: ['invoice', resolvedId] });
          onChanged?.();
        }}
      />
    </>
  );
}
