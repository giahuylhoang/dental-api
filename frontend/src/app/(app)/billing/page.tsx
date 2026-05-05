'use client';

import React from 'react';
import { KpiTile } from '@/components/domain/KpiTile';
import { StatusPill } from '@/components/domain/StatusPill';
import { useToast } from '@/components/overlays/ToastContext';
import { Drawer } from '@/components/overlays/Drawer';
import { CenterModal } from '@/components/overlays/CenterModal';
import { ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api';

interface Invoice {
  id: string;
  patient: string;
  created: string;
  total: number;
  balance: number;
  status: string;
  insurance: string;
}

interface Claim {
  id: string;
  invoice: string;
  carrier: string;
  kind: string;
  status: string;
  submitted: string;
  accepted: number | null;
}

const SEED_INVOICES: Invoice[] = [
  { id: 'INV-2026-0418', patient: 'Alice Stevens', created: '2026-04-30', total: 609.00, balance: 0.00, status: 'paid', insurance: 'Alberta Blue Cross' },
  { id: 'INV-2026-0417', patient: 'Priya Khanna', created: '2026-04-30', total: 971.25, balance: 314.10, status: 'partial', insurance: 'Manulife' },
  { id: 'INV-2026-0416', patient: 'Sofía Castillo', created: '2026-04-29', total: 299.25, balance: 299.25, status: 'issued', insurance: 'Alberta Health' },
  { id: 'INV-2026-0414', patient: 'Marcus Doan', created: '2026-04-28', total: 152.25, balance: 0.00, status: 'paid', insurance: 'Sun Life' },
  { id: 'INV-2026-0413', patient: 'Eli Brouwer', created: '2026-04-26', total: 89.25, balance: 89.25, status: 'overdue', insurance: 'Canada Life' },
  { id: 'INV-2026-0411', patient: 'Daniel Okafor', created: '2026-04-22', total: 252.00, balance: 252.00, status: 'overdue', insurance: 'Pacific Blue Cross' },
  { id: 'INV-2026-0410', patient: 'Rae Tomlinson', created: '2026-04-21', total: 327.60, balance: 0.00, status: 'paid', insurance: 'Alberta Blue Cross' },
  { id: 'INV-2026-0408', patient: 'Yuki Tanaka', created: '2026-04-20', total: 183.75, balance: 0.00, status: 'draft', insurance: 'Self pay' },
];

const SEED_CLAIMS: Claim[] = [
  { id: 'CLM-9831', invoice: 'INV-2026-0417', carrier: 'Manulife', kind: 'predetermination', status: 'submitted', submitted: '2026-04-30', accepted: null },
  { id: 'CLM-9826', invoice: 'INV-2026-0416', carrier: 'Alberta Health', kind: 'standard', status: 'adjudicated', submitted: '2026-04-29', accepted: 220.00 },
  { id: 'CLM-9821', invoice: 'INV-2026-0413', carrier: 'Canada Life', kind: 'standard', status: 'paid', submitted: '2026-04-26', accepted: 72.40 },
  { id: 'CLM-9818', invoice: 'INV-2026-0411', carrier: 'Pacific Blue Cross', kind: 'standard', status: 'submitted', submitted: '2026-04-23', accepted: null },
  { id: 'CLM-9810', invoice: 'INV-2026-0410', carrier: 'Alberta Blue Cross', kind: 'standard', status: 'paid', submitted: '2026-04-21', accepted: 261.00 },
];

const FILTERS = ['All', 'Issued', 'Partial', 'Paid', 'Overdue', 'Draft'];
const INVOICE_STATUSES = ['draft', 'issued', 'partial', 'paid', 'overdue', 'void'];
const INSURANCE_OPTIONS = ['Alberta Blue Cross', 'Manulife', 'Alberta Health', 'Sun Life', 'Canada Life', 'Pacific Blue Cross', 'Self pay'];
const CLAIM_STATUSES = ['submitted', 'adjudicated', 'paid', 'rejected'];
const CLAIM_KINDS = ['standard', 'predetermination'];
const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });

export default function BillingPage() {
  const { addToast } = useToast();
  const [invoices, setInvoices] = React.useState<Invoice[]>(SEED_INVOICES);
  const [claims, setClaims] = React.useState<Claim[]>(SEED_CLAIMS);
  const [filter, setFilter] = React.useState('All');
  const [query, setQuery] = React.useState('');
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [newInvoicePatient, setNewInvoicePatient] = React.useState('Alice Stevens');
  const [newInvoiceService, setNewInvoiceService] = React.useState('E04');
  const [submitting, setSubmitting] = React.useState(false);

  const [invoiceId, setInvoiceId] = React.useState<string | null>(null);
  const [invoiceEditing, setInvoiceEditing] = React.useState(false);
  const [invoiceDraft, setInvoiceDraft] = React.useState<Invoice | null>(null);
  const detailInvoice = invoiceId ? invoices.find(i => i.id === invoiceId) ?? null : null;

  const [claimId, setClaimId] = React.useState<string | null>(null);
  const [claimEditing, setClaimEditing] = React.useState(false);
  const [claimDraft, setClaimDraft] = React.useState<Claim | null>(null);
  const detailClaim = claimId ? claims.find(c => c.id === claimId) ?? null : null;

  const SERVICE_PRICES: Record<string, number> = { E04: 145, I02: 95, C01: 580, D01: 285 };

  const handleCreateInvoice = async () => {
    setSubmitting(true);
    try {
      const price = SERVICE_PRICES[newInvoiceService] || 145;
      const res = await api.v2.billing.invoices.create({
        patient_id: newInvoicePatient.replace(/\s/g, '-').toLowerCase(),
        lines: [{ procedure_code: newInvoiceService, description: newInvoiceService, qty: 1, unit_price: price }],
      }) as { id: string; total: number; balance: number; status: string };
      await api.v2.billing.invoices.issue(res.id);
      const newInv: Invoice = {
        id: res.id,
        patient: newInvoicePatient,
        created: new Date().toISOString().slice(0, 10),
        total: res.total,
        balance: res.balance,
        status: 'issued',
        insurance: 'Self pay',
      };
      setInvoices(prev => [newInv, ...prev]);
      addToast('Invoice created.', res.id);
      setDrawerOpen(false);
    } catch (e) {
      addToast('Failed to create invoice.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarkPaid = async (invId: string, amount: number) => {
    try {
      await api.v2.billing.invoices.pay(invId, { method: 'cash', amount });
      setInvoices(prev => prev.map(i => i.id === invId ? { ...i, balance: 0, status: 'paid' } : i));
      addToast(`${invId} marked paid.`, invId);
      closeInvoice();
    } catch { addToast('Failed to mark paid.'); }
  };

  const handleSubmitClaim = async (invoiceId: string, carrier: string) => {
    try {
      const res = await api.v2.insurance.claims.create({ invoice_id: invoiceId, carrier, kind: 'standard' }) as { id: string };
      await api.v2.insurance.claims.submit(res.id);
      const newClaim: Claim = {
        id: res.id,
        invoice: invoiceId,
        carrier,
        kind: 'standard',
        status: 'submitted',
        submitted: new Date().toISOString().slice(0, 10),
        accepted: null,
      };
      setClaims(prev => [newClaim, ...prev]);
      addToast('Claim submitted.', res.id);
    } catch { addToast('Failed to submit claim.'); }
  };

  const totalRevenue = invoices.reduce((s, i) => s + i.total, 0);
  const totalOutstanding = invoices.reduce((s, i) => s + i.balance, 0);

  const filtered = invoices.filter(i => {
    if (filter === 'All') return true;
    if (filter === 'Issued') return i.status === 'issued';
    if (filter === 'Partial') return i.status === 'partial';
    if (filter === 'Paid') return i.status === 'paid';
    if (filter === 'Overdue') return i.status === 'overdue';
    if (filter === 'Draft') return i.status === 'draft';
    return true;
  }).filter(i => !query || i.patient.toLowerCase().includes(query.toLowerCase()) || i.id.toLowerCase().includes(query.toLowerCase()));

  const startInvoiceEdit = () => { if (detailInvoice) { setInvoiceDraft({ ...detailInvoice }); setInvoiceEditing(true); } };
  const saveInvoiceEdit = () => {
    if (!invoiceDraft) return;
    setInvoices(prev => prev.map(i => (i.id === invoiceDraft.id ? invoiceDraft : i)));
    addToast(`${invoiceDraft.id} updated.`, invoiceDraft.id);
    setInvoiceEditing(false);
    setInvoiceDraft(null);
  };
  const closeInvoice = () => { setInvoiceId(null); setInvoiceEditing(false); setInvoiceDraft(null); };

  const startClaimEdit = () => { if (detailClaim) { setClaimDraft({ ...detailClaim }); setClaimEditing(true); } };
  const saveClaimEdit = () => {
    if (!claimDraft) return;
    setClaims(prev => prev.map(c => (c.id === claimDraft.id ? claimDraft : c)));
    addToast(`${claimDraft.id} updated.`, claimDraft.id);
    setClaimEditing(false);
    setClaimDraft(null);
  };
  const closeClaim = () => { setClaimId(null); setClaimEditing(false); setClaimDraft(null); };

  return (
    <>
      <style>{`
        .aging-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
        .aging-cell{border:1px solid var(--rr-parchment);border-radius:6px;padding:14px 16px;background:#fff}
        .aging-label{font-family:var(--font-ui);font-size:.68rem;color:var(--rr-slate-dark);letter-spacing:.08em;text-transform:uppercase}
        .aging-amount{font-family:var(--font-mono);font-size:1.2rem;font-weight:600;color:var(--rr-navy-800);margin-top:4px}
        .aging-bar-track{height:4px;background:var(--rr-parchment);border-radius:999px;margin-top:10px;overflow:hidden}
        .aging-bar-fill{height:100%;background:var(--rr-steel-500)}
        .aging-bar-fill-warn{height:100%;background:#B45309}
        .aging-bar-fill-danger{height:100%;background:#9B2335}
      `}</style>

      <div className="page-header">
        <div><h1 className="page-title">Billing</h1><div className="page-sub">{invoices.length} invoices · {fmt.format(totalRevenue)} total · {fmt.format(totalOutstanding)} outstanding</div></div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost btn-md" onClick={() => addToast('Billing export ready.')}>Export</button>
          <button className="btn btn-primary btn-md" onClick={() => setDrawerOpen(true)}>+ New invoice</button>
        </div>
      </div>

      <div className="kpi-row">
        <KpiTile label="Total Revenue" value={fmt.format(totalRevenue)} delta="+ 8.2%" trend="up" accent="steel" />
        <KpiTile label="Outstanding" value={fmt.format(totalOutstanding)} delta="+ 2.1%" trend="down" accent="navy" />
        <KpiTile label="Paid this month" value={fmt.format(invoices.filter(i => i.status === 'paid').reduce((s, i) => s + i.total, 0))} delta="+ 12%" trend="up" accent="steel" />
        <KpiTile label="Collection Rate" value="84%" delta="+ 1.5%" trend="up" accent="steel" />
      </div>

      <div className="aging-grid">
        {[{ label: '0–30 days', amt: 4280, pct: 42, cls: '' }, { label: '31–60 days', amt: 2180, pct: 21, cls: '' }, { label: '61–90 days', amt: 1450, pct: 14, cls: 'warn' }, { label: '91–120 days', amt: 890, pct: 9, cls: 'warn' }, { label: '120+ days', amt: 1410, pct: 14, cls: 'danger' }].map(a => (
          <div key={a.label} className="aging-cell">
            <div className="aging-label">{a.label}</div><div className="aging-amount">{fmt.format(a.amt)}</div>
            <div className="aging-bar-track"><div className={a.cls === 'warn' ? 'aging-bar-fill-warn' : a.cls === 'danger' ? 'aging-bar-fill-danger' : 'aging-bar-fill'} style={{ width: a.pct + '%' }} /></div>
          </div>
        ))}
      </div>

      <div className="panel" style={{ padding: '14px 18px' }}>
        <div className="toolbar" style={{ marginBottom: 14 }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 220 }}>
            <svg style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#8A9BB0' }} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
            <input type="text" placeholder="Search invoices or patients..." value={query} onChange={e => setQuery(e.target.value)}
              style={{ flex: 1, minWidth: 220, height: 36, padding: '0 12px 0 36px', borderRadius: 4, border: '1px solid #EDE9E0', background: '#FAF9F6', fontFamily: "'Inter', sans-serif", fontSize: '.85rem', color: '#1C2333', width: '100%' }} />
          </div>
          {FILTERS.map(f => (<button key={f} className={'filter-pill' + (filter === f ? ' active' : '')} onClick={() => setFilter(f)}>{f}</button>))}
        </div>
        <table className="list">
          <thead><tr><th>Invoice</th><th>Patient</th><th>Created</th><th>Insurance</th><th style={{ textAlign: 'right' }}>Total</th><th style={{ textAlign: 'right' }}>Balance</th><th>Status</th></tr></thead>
          <tbody>
            {filtered.map(i => (
              <tr key={i.id} style={{ cursor: 'pointer' }} onClick={() => { setInvoiceId(i.id); setInvoiceEditing(false); }}>
                <td className="id-cell">{i.id}</td><td style={{ fontWeight: 600, color: '#1C2333' }}>{i.patient}</td><td className="id-cell">{i.created}</td>
                <td style={{ color: '#4A5568' }}>{i.insurance}</td>
                <td className="num" style={{ textAlign: 'right' }}>{fmt.format(i.total)}</td>
                <td className="num" style={{ textAlign: 'right', color: i.balance > 0 ? '#B45309' : '#4A5568' }}>{fmt.format(i.balance)}</td>
                <td><StatusPill status={i.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <div className="panel-header"><div><div className="panel-h-title">Insurance Claims</div><div className="panel-h-sub">{claims.length} claims · {claims.filter(c => c.status === 'submitted').length} pending</div></div><span className="panel-h-action">Submit new claim →</span></div>
        <table className="list">
          <thead><tr><th>Claim</th><th>Invoice</th><th>Carrier</th><th>Kind</th><th>Status</th><th>Submitted</th><th>Accepted</th></tr></thead>
          <tbody>
            {claims.map(c => (
              <tr key={c.id} style={{ cursor: 'pointer' }} onClick={() => { setClaimId(c.id); setClaimEditing(false); }}>
                <td className="id-cell">{c.id}</td><td className="id-cell">{c.invoice}</td><td>{c.carrier}</td>
                <td><span className="pill" style={{ background: c.kind === 'predetermination' ? '#FDF3E5' : '#D9EAF5', color: c.kind === 'predetermination' ? '#B45309' : '#2E6494' }}>{c.kind}</span></td>
                <td><StatusPill status={c.status} /></td><td className="id-cell">{c.submitted}</td>
                <td className="num" style={{ fontFamily: 'var(--font-mono)', fontSize: '.82rem' }}>{c.accepted ? fmt.format(c.accepted) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>ROCKYRIDGE · DENTAL AI · v1</div>

      {drawerOpen && (
        <Drawer open={true} onClose={() => setDrawerOpen(false)} meta="New invoice" title="Create invoice" sub="Add line items and issue."
          footer={<><button className="btn btn-ghost btn-md" onClick={() => setDrawerOpen(false)}>Cancel</button><button className="btn btn-primary btn-md" disabled={submitting} onClick={handleCreateInvoice}>{submitting ? 'Creating...' : 'Issue invoice'}</button></>}
        >
          <div className="field"><label className="lbl">Patient</label><select className="d-input" value={newInvoicePatient} onChange={e => setNewInvoicePatient(e.target.value)}>{['Alice Stevens', 'Marcus Doan', 'Priya Khanna', 'Eli Brouwer', 'Sofía Castillo', 'Daniel Okafor'].map(n => <option key={n}>{n}</option>)}</select></div>
          <div className="field"><label className="lbl">Service</label><select className="d-input" value={newInvoiceService} onChange={e => setNewInvoiceService(e.target.value)}><option value="E04">E04 · Periodic exam · $145</option><option value="I02">I02 · Scaling · $95</option><option value="C01">C01 · Crown prep · $580</option><option value="D01">D01 · Denture reline · $285</option></select></div>
          <div className="field"><label className="lbl">Date</label><input type="date" className="d-input" defaultValue="2026-05-04" /></div>
          <div className="field"><label className="lbl">Notes</label><textarea className="d-textarea" placeholder="Invoice notes..." /></div>
        </Drawer>
      )}

      {/* Invoice detail modal */}
      {detailInvoice && (
        <CenterModal open={true} onClose={closeInvoice} width="min(560px, 92vw)">
          <div className="center-modal-topbar"><button className="drawer-back" onClick={closeInvoice}><ArrowLeft size={18} strokeWidth={1.5} /></button><span className="back-label">{invoiceEditing ? 'Editing invoice' : 'Back to Billing'}</span></div>
          <div className="center-modal-body">
            <div className="appt-ws-hero">
              <div className="appt-ws-ava">{detailInvoice.patient.split(' ').map(s => s[0]).join('').toUpperCase()}</div>
              <div className="appt-ws-info">
                <div className="appt-ws-name">{detailInvoice.patient}</div>
                <div className="appt-ws-detail">{detailInvoice.id}</div>
                <div className="appt-ws-id">{detailInvoice.created}</div>
              </div>
              <StatusPill status={(invoiceEditing && invoiceDraft ? invoiceDraft.status : detailInvoice.status)} />
            </div>

            {!invoiceEditing && (
              <div>
                <div className="detail-row"><span className="detail-k">Patient</span><span className="detail-v">{detailInvoice.patient}</span></div>
                <div className="detail-row"><span className="detail-k">Total</span><span className="detail-v" style={{ fontFamily: 'var(--font-mono)' }}>{fmt.format(detailInvoice.total)}</span></div>
                <div className="detail-row"><span className="detail-k">Balance</span><span className="detail-v" style={{ fontFamily: 'var(--font-mono)', color: detailInvoice.balance > 0 ? '#B45309' : '#4A5568' }}>{fmt.format(detailInvoice.balance)}</span></div>
                <div className="detail-row"><span className="detail-k">Insurance</span><span className="detail-v">{detailInvoice.insurance}</span></div>
                <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v">{detailInvoice.status}</span></div>
              </div>
            )}

            {invoiceEditing && invoiceDraft && (
              <div>
                <div className="field-row">
                  <div className="field"><label className="lbl">Total</label><input className="d-input" type="number" step="0.01" value={invoiceDraft.total} onChange={e => setInvoiceDraft({ ...invoiceDraft, total: Number(e.target.value) || 0 })} /></div>
                  <div className="field"><label className="lbl">Balance</label><input className="d-input" type="number" step="0.01" value={invoiceDraft.balance} onChange={e => setInvoiceDraft({ ...invoiceDraft, balance: Number(e.target.value) || 0 })} /></div>
                </div>
                <div className="field"><label className="lbl">Insurance</label>
                  <select className="d-input" value={invoiceDraft.insurance} onChange={e => setInvoiceDraft({ ...invoiceDraft, insurance: e.target.value })}>
                    {INSURANCE_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div className="field"><label className="lbl">Status</label>
                  <select className="d-input" value={invoiceDraft.status} onChange={e => setInvoiceDraft({ ...invoiceDraft, status: e.target.value })}>
                    {INVOICE_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: 8 }}>
              {!invoiceEditing && <><button className="btn btn-primary btn-md" onClick={startInvoiceEdit}>Edit invoice</button>{detailInvoice.balance > 0 && <button className="btn btn-ghost btn-md" onClick={() => handleMarkPaid(detailInvoice.id, detailInvoice.balance)}>Mark paid</button>}{detailInvoice.insurance !== 'Self pay' && <button className="btn btn-ghost btn-md" onClick={() => handleSubmitClaim(detailInvoice.id, detailInvoice.insurance)}>Submit claim</button>}<button className="btn btn-ghost btn-md" onClick={closeInvoice}>Close</button></>}
              {invoiceEditing && <><button className="btn btn-primary btn-md" onClick={saveInvoiceEdit}>Save changes</button><button className="btn btn-ghost btn-md" onClick={() => { setInvoiceEditing(false); setInvoiceDraft(null); }}>Cancel</button></>}
            </div>
          </div>
        </CenterModal>
      )}

      {/* Claim detail modal */}
      {detailClaim && (
        <CenterModal open={true} onClose={closeClaim} width="min(540px, 92vw)">
          <div className="center-modal-topbar"><button className="drawer-back" onClick={closeClaim}><ArrowLeft size={18} strokeWidth={1.5} /></button><span className="back-label">{claimEditing ? 'Editing claim' : 'Back to Billing'}</span></div>
          <div className="center-modal-body">
            <div className="appt-ws-hero">
              <div className="appt-ws-ava">{detailClaim.carrier.split(' ').map(s => s[0]).join('').toUpperCase().slice(0, 2)}</div>
              <div className="appt-ws-info">
                <div className="appt-ws-name">{detailClaim.carrier}</div>
                <div className="appt-ws-detail">Claim {detailClaim.id}</div>
                <div className="appt-ws-id">{detailClaim.invoice} · submitted {detailClaim.submitted}</div>
              </div>
              <StatusPill status={(claimEditing && claimDraft ? claimDraft.status : detailClaim.status)} />
            </div>

            {!claimEditing && (
              <div>
                <div className="detail-row"><span className="detail-k">Claim ID</span><span className="detail-v">{detailClaim.id}</span></div>
                <div className="detail-row"><span className="detail-k">Invoice</span><span className="detail-v">{detailClaim.invoice}</span></div>
                <div className="detail-row"><span className="detail-k">Carrier</span><span className="detail-v">{detailClaim.carrier}</span></div>
                <div className="detail-row"><span className="detail-k">Kind</span><span className="detail-v">{detailClaim.kind}</span></div>
                <div className="detail-row"><span className="detail-k">Submitted</span><span className="detail-v">{detailClaim.submitted}</span></div>
                <div className="detail-row"><span className="detail-k">Accepted</span><span className="detail-v" style={{ fontFamily: 'var(--font-mono)' }}>{detailClaim.accepted ? fmt.format(detailClaim.accepted) : '—'}</span></div>
              </div>
            )}

            {claimEditing && claimDraft && (
              <div>
                <div className="field-row">
                  <div className="field"><label className="lbl">Kind</label>
                    <select className="d-input" value={claimDraft.kind} onChange={e => setClaimDraft({ ...claimDraft, kind: e.target.value })}>
                      {CLAIM_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                    </select>
                  </div>
                  <div className="field"><label className="lbl">Status</label>
                    <select className="d-input" value={claimDraft.status} onChange={e => setClaimDraft({ ...claimDraft, status: e.target.value })}>
                      {CLAIM_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
                <div className="field"><label className="lbl">Accepted amount</label><input className="d-input" type="number" step="0.01" value={claimDraft.accepted ?? ''} onChange={e => setClaimDraft({ ...claimDraft, accepted: e.target.value === '' ? null : Number(e.target.value) })} /></div>
              </div>
            )}

            <div style={{ display: 'flex', gap: 8 }}>
              {!claimEditing && <><button className="btn btn-primary btn-md" onClick={startClaimEdit}>Edit claim</button><button className="btn btn-ghost btn-md" onClick={closeClaim}>Close</button></>}
              {claimEditing && <><button className="btn btn-primary btn-md" onClick={saveClaimEdit}>Save changes</button><button className="btn btn-ghost btn-md" onClick={() => { setClaimEditing(false); setClaimDraft(null); }}>Cancel</button></>}
            </div>
          </div>
        </CenterModal>
      )}
    </>
  );
}
