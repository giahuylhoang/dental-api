'use client';

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { KpiTile } from '@/components/dental/KpiTile';
import { StatusPill } from '@/components/dental/StatusPill';
import { Drawer } from '@/components/dental/Drawer';
import { fetcher } from '@/lib/api/client';

const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });

// TODO: wire to dental-agent — endpoint not yet implemented
const SEED_AR_AGING = [
  { label: 'Current',    amount: 4860.20, pct: 60, kind: '' },
  { label: '1–30 days',  amount: 1245.50, pct: 35, kind: '' },
  { label: '31–60 days', amount:  612.10, pct: 22, kind: 'warn' },
  { label: '61–90 days', amount:  341.25, pct: 12, kind: 'warn' },
  { label: '90+ days',   amount:  252.00, pct:  8, kind: 'danger' },
];

// TODO: wire to dental-agent — endpoint not yet implemented
const SEED_CLAIMS = [
  { id: 'CLM-9831', invoice: 'INV-2026-0417', carrier: 'Manulife',           kind: 'predetermination', status: 'submitted',   submitted: '2026-04-30', accepted: null   },
  { id: 'CLM-9826', invoice: 'INV-2026-0416', carrier: 'Alberta Health',     kind: 'standard',         status: 'adjudicated', submitted: '2026-04-29', accepted: 220.00 },
  { id: 'CLM-9821', invoice: 'INV-2026-0413', carrier: 'Canada Life',        kind: 'standard',         status: 'paid',        submitted: '2026-04-26', accepted:  72.40 },
  { id: 'CLM-9818', invoice: 'INV-2026-0411', carrier: 'Pacific Blue Cross', kind: 'standard',         status: 'submitted',   submitted: '2026-04-23', accepted: null   },
  { id: 'CLM-9810', invoice: 'INV-2026-0410', carrier: 'Alberta Blue Cross', kind: 'standard',         status: 'paid',        submitted: '2026-04-21', accepted: 261.00 },
];

interface Invoice {
  id: string;
  invoice_number?: string;
  patient_id: string;
  patient_name?: string;
  insurance?: string;
  status: string;
  subtotal: number;
  gst: number;
  total: number;
  balance: number;
  created_at: string;
}

const FILTERS = ['All', 'Issued', 'Partial', 'Paid', 'Overdue', 'Draft'];

function AgingBar({ pct, kind }: { pct: number; kind: string }) {
  const fillColor = kind === 'danger' ? '#9B2335' : kind === 'warn' ? '#B45309' : 'var(--rr-steel-500, #3A7FBD)';
  return (
    <div style={{ height: 4, background: 'var(--rr-parchment, #EDE9E0)', borderRadius: 999, marginTop: 10, overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${pct}%`, background: fillColor }} />
    </div>
  );
}

export default function BillingPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState('All');
  const [query, setQuery] = useState('');
  const [toasts, setToasts] = useState<{ id: number; msg: string }[]>([]);
  const [drawerInvoiceId, setDrawerInvoiceId] = useState<string | null>(null);

  const addToast = (msg: string) => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3000);
  };

  const { data: invoices = [] } = useQuery<Invoice[]>({
    queryKey: ['invoices'],
    queryFn: () => fetcher<Invoice[]>('/api/v2/billing/invoices'),
  });

  const rows = invoices.filter(i => {
    if (filter !== 'All' && i.status !== filter.toLowerCase()) return false;
    if (query) {
      const q = query.toLowerCase();
      const num = i.invoice_number ?? i.id;
      const name = i.patient_name ?? i.patient_id;
      const ins = i.insurance ?? '';
      if (!`${num} ${name} ${ins}`.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const outstanding = invoices.filter(i => ['issued', 'partial', 'overdue'].includes(i.status)).reduce((s, i) => s + i.balance, 0);
  const overdue = invoices.filter(i => i.status === 'overdue').reduce((s, i) => s + i.balance, 0);
  const collected30 = invoices.filter(i => i.status === 'paid').reduce((s, i) => s + i.total, 0);
  const claimsOpen = SEED_CLAIMS.filter(c => c.status === 'submitted').length;

  return (
    <>
      <div style={{ padding: '28px 32px', display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 1280, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>

        {/* Page header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontWeight: 800, fontSize: '1.8rem', color: 'var(--rr-navy-800, #1C2333)', letterSpacing: '-.025em', margin: '0 0 4px' }}>Billing</h1>
            <div style={{ fontSize: '.88rem', color: 'var(--rr-slate-dark, #4A5568)' }}>
              {fmt.format(outstanding)} outstanding · {invoices.length} invoices · 5 active claims · 1 overdue
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-ghost btn-md" onClick={() => addToast('Ledger exported — ledger_2026-05-03.csv')}>Export ledger</button>
            <button className="btn btn-ghost btn-md" onClick={() => addToast('New claim form would open here.')}>+ New claim</button>
            <button className="btn btn-primary btn-md" onClick={() => addToast('New invoice form would open here.')}>+ New invoice</button>
          </div>
        </div>

        {/* KPI strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
          <KpiTile label="Outstanding"     value={fmt.format(outstanding)} delta="– 4.1%"  trend="up"   accent="steel" />
          <KpiTile label="Overdue 30+"     value={fmt.format(overdue)}     delta="+ 12%"   trend="down" accent="navy"  />
          <KpiTile label="Collected · 30d" value={fmt.format(collected30)} delta="+ 8.4%"  trend="up"   accent="steel" />
          <KpiTile label="Claims · open"   value={String(claimsOpen)}      delta="– 2"     trend="up"   accent="steel" />
        </div>

        {/* A/R aging */}
        <div style={{ background: '#fff', border: '1px solid var(--rr-parchment, #EDE9E0)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs, 0 1px 3px rgba(0,0,0,.06))' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800, #1C2333)' }}>Accounts receivable · aging</div>
              <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark, #4A5568)', marginTop: 2 }}>Balance owed by bucket · across all carriers and self-pay</div>
            </div>
            <span style={{ fontSize: '.82rem', color: 'hsl(var(--primary))', cursor: 'pointer' }}>View AR report →</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
            {SEED_AR_AGING.map(b => (
              <div key={b.label} style={{ border: '1px solid var(--rr-parchment, #EDE9E0)', borderRadius: 6, padding: '14px 16px' }}>
                <div style={{ fontSize: '.68rem', color: 'var(--rr-slate-dark, #4A5568)', letterSpacing: '.08em', textTransform: 'uppercase' }}>{b.label}</div>
                <div style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: '1.2rem', fontWeight: 600, color: 'var(--rr-navy-800, #1C2333)', marginTop: 4 }}>{fmt.format(b.amount)}</div>
                <AgingBar pct={b.pct} kind={b.kind} />
              </div>
            ))}
          </div>
        </div>

        {/* Invoices table */}
        <div style={{ background: '#fff', border: '1px solid var(--rr-parchment, #EDE9E0)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs, 0 1px 3px rgba(0,0,0,.06))' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800, #1C2333)' }}>Invoices</div>
              <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark, #4A5568)', marginTop: 2 }}>Showing {rows.length} of {invoices.length}</div>
            </div>
            <span style={{ fontSize: '.82rem', color: 'hsl(var(--primary))', cursor: 'pointer' }}>Open in editor →</span>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 }}>
            <input
              type="search"
              placeholder="Search by invoice #, patient, or carrier…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              style={{ flex: 1, minWidth: 220, height: 36, padding: '0 12px', borderRadius: 4, border: '1px solid var(--rr-parchment, #EDE9E0)', fontSize: '.85rem' }}
            />
            {FILTERS.map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  display: 'inline-flex', alignItems: 'center', height: 32, padding: '0 12px',
                  borderRadius: 999, border: '1px solid var(--rr-parchment, #EDE9E0)',
                  background: filter === f ? 'var(--rr-mist, #EEF3F8)' : '#fff',
                  color: filter === f ? 'var(--rr-navy-800, #1C2333)' : 'var(--rr-slate-dark, #4A5568)',
                  fontWeight: filter === f ? 600 : 400, fontSize: '.76rem', cursor: 'pointer',
                }}
              >{f}</button>
            ))}
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '.85rem' }}>
            <thead>
              <tr>
                {['Invoice #', 'Patient', 'Insurance', 'Created', 'Total', 'Balance', 'Status'].map((h, i) => (
                  <th key={h} style={{ textAlign: i >= 4 && i <= 5 ? 'right' : 'left', padding: '12px 14px', color: 'var(--rr-slate-dark, #4A5568)', fontSize: '.68rem', letterSpacing: '.08em', textTransform: 'uppercase', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(i => (
                <tr key={i.id} style={{ cursor: 'pointer' }} onClick={() => setDrawerInvoiceId(i.id)}>
                  <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontFamily: 'var(--font-mono, monospace)', fontSize: '.76rem', color: '#3A7FBD', fontWeight: 600 }}>{i.invoice_number ?? i.id}</td>
                  <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontWeight: 600, color: '#1C2333' }}>{i.patient_name ?? i.patient_id}</td>
                  <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)' }}>{i.insurance ?? '—'}</td>
                  <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontFamily: 'var(--font-mono, monospace)', fontSize: '.76rem', color: 'var(--rr-slate-dark, #4A5568)' }}>{i.created_at?.slice(0, 10)}</td>
                  <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', textAlign: 'right', fontFamily: 'var(--font-mono, monospace)', fontSize: '.82rem' }}>{fmt.format(i.total)}</td>
                  <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', textAlign: 'right', fontFamily: 'var(--font-mono, monospace)', fontSize: '.82rem', color: i.balance > 0 ? '#B45309' : '#4A5568' }}>{fmt.format(i.balance)}</td>
                  <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)' }}><StatusPill kind="invoice" value={i.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Insurance claims + Adjudicate panel */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 18, alignItems: 'flex-start' }}>
          {/* Insurance claims table */}
          <div style={{ background: '#fff', border: '1px solid var(--rr-parchment, #EDE9E0)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs, 0 1px 3px rgba(0,0,0,.06))' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800, #1C2333)' }}>Insurance claims</div>
                <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark, #4A5568)', marginTop: 2 }}>Last 14 days · Draft → Submitted → Adjudicated → Paid</div>
              </div>
              <span style={{ fontSize: '.82rem', color: 'hsl(var(--primary))', cursor: 'pointer' }}>All claims →</span>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '.85rem' }}>
              <thead>
                <tr>
                  {['Claim #', 'Invoice', 'Carrier', 'Kind', 'Submitted', 'Accepted', 'Status'].map((h, i) => (
                    <th key={h} style={{ textAlign: i === 5 ? 'right' : 'left', padding: '12px 14px', color: 'var(--rr-slate-dark, #4A5568)', fontSize: '.68rem', letterSpacing: '.08em', textTransform: 'uppercase', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {SEED_CLAIMS.map(c => (
                  <tr key={c.id} style={{ cursor: 'pointer' }}>
                    <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontFamily: 'var(--font-mono, monospace)', fontSize: '.76rem', color: '#3A7FBD', fontWeight: 600 }}>{c.id}</td>
                    <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontFamily: 'var(--font-mono, monospace)', fontSize: '.76rem', color: 'var(--rr-slate-dark, #4A5568)' }}>{c.invoice}</td>
                    <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)' }}>{c.carrier}</td>
                    <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', color: '#4A5568' }}>{c.kind}</td>
                    <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', fontFamily: 'var(--font-mono, monospace)', fontSize: '.76rem', color: 'var(--rr-slate-dark, #4A5568)' }}>{c.submitted}</td>
                    <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)', textAlign: 'right', fontFamily: 'var(--font-mono, monospace)', fontSize: '.82rem' }}>{c.accepted == null ? '—' : fmt.format(c.accepted)}</td>
                    <td style={{ padding: '14px', borderBottom: '1px solid var(--rr-parchment, #EDE9E0)' }}><StatusPill kind="claim" value={c.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Adjudicate next claim */}
          <div style={{ background: '#fff', border: '1px solid var(--rr-parchment, #EDE9E0)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs, 0 1px 3px rgba(0,0,0,.06))' }}>
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800, #1C2333)' }}>Adjudicate next claim</div>
              <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark, #4A5568)', marginTop: 2 }}>CLM-9831 · Manulife · INV-2026-0417 · Priya Khanna</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '.85rem' }}>
              <label style={{ color: '#4A5568', fontSize: '.74rem', textTransform: 'uppercase', letterSpacing: '.08em', fontWeight: 600 }}>Outcome</label>
              <select style={{ height: 36, padding: '0 10px', border: '1px solid #EDE9E0', borderRadius: 4, color: '#1C2333' }}>
                <option>Accepted in full</option>
                <option>Accepted partial</option>
                <option>Rejected — patient liability</option>
                <option>Rejected — needs predetermination</option>
              </select>

              <label style={{ color: '#4A5568', fontSize: '.74rem', textTransform: 'uppercase', letterSpacing: '.08em', fontWeight: 600 }}>Accepted amount</label>
              <input type="text" defaultValue="$657.15" style={{ height: 36, padding: '0 10px', border: '1px solid #EDE9E0', borderRadius: 4, color: '#1C2333', fontFamily: 'var(--font-mono, monospace)' }} />

              <label style={{ color: '#4A5568', fontSize: '.74rem', textTransform: 'uppercase', letterSpacing: '.08em', fontWeight: 600 }}>Response codes</label>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {['E04', 'I02', 'X11'].map(c => (
                  <span key={c} style={{ fontSize: '.66rem', fontWeight: 600, padding: '3px 10px', borderRadius: 999, background: '#F5F2EC', color: '#4A5568', fontFamily: 'var(--font-mono, monospace)' }}>{c}</span>
                ))}
              </div>

              <label style={{ color: '#4A5568', fontSize: '.74rem', textTransform: 'uppercase', letterSpacing: '.08em', fontWeight: 600 }}>Notes</label>
              <textarea rows={3} placeholder="Carrier remarks…" style={{ padding: 10, border: '1px solid #EDE9E0', borderRadius: 4, fontSize: '.85rem', color: '#1C2333', resize: 'vertical' }} />

              <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                <button className="btn btn-ghost btn-sm" onClick={() => addToast('Draft saved.')}>Save draft</button>
                <button className="btn btn-primary btn-sm" onClick={() => addToast('Adjudication saved.')}>Save adjudication</button>
              </div>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', padding: '20px 0', fontSize: '.72rem', color: 'var(--rr-slate, #8A9BB0)', letterSpacing: '.06em' }}>
          ROCKYRIDGE · DENTAL AI · v1
        </div>
      </div>

      {/* Invoice drawer */}
      <Drawer open={drawerInvoiceId !== null} onClose={() => setDrawerInvoiceId(null)} title={drawerInvoiceId ?? 'Invoice'}>
        <p style={{ fontSize: '.85rem', color: 'var(--rr-slate-dark, #4A5568)' }}>Invoice detail for {drawerInvoiceId}</p>
      </Drawer>

      {/* Toasts */}
      {toasts.length > 0 && (
        <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 100, display: 'flex', flexDirection: 'column', gap: 8, pointerEvents: 'none' }}>
          {toasts.map(t => (
            <div key={t.id} style={{ background: 'var(--rr-navy-800, #1C2333)', color: '#fff', padding: '12px 18px', borderRadius: 6, fontSize: '.85rem', boxShadow: '0 4px 16px rgba(10,25,47,0.22)', pointerEvents: 'auto', maxWidth: 380 }}>
              {t.msg}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
