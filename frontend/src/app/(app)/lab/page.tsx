'use client';

import React from 'react';
import { KpiTile } from '@/components/domain/KpiTile';
import { LabPipeline } from '@/components/domain/LabPipeline';
import { StatusPill } from '@/components/domain/StatusPill';
import { useToast } from '@/components/overlays/ToastContext';
import { Drawer } from '@/components/overlays/Drawer';
import { CenterModal } from '@/components/overlays/CenterModal';
import { ArrowLeft } from 'lucide-react';
import type { LabCase } from '@/lib/data';

type Col = 'sent' | 'progress' | 'returned' | 'overdue';

interface LabCaseRow {
  id: string;
  patient: string;
  vendor: string;
  item: string;
  sent: string;
  eta: string;
  col: Col;
}

const SEED_CASES: LabCaseRow[] = [
  { id: 'LC-2026-0481', patient: 'Alice Stevens', vendor: 'Pinnacle Dental Lab', item: 'Crown · #36', sent: '2026-04-28', eta: '2026-05-12', col: 'sent' },
  { id: 'LC-2026-0476', patient: 'Sofía Castillo', vendor: 'Crown City Lab', item: 'Implant abutment · #11', sent: '2026-04-26', eta: '2026-05-18', col: 'sent' },
  { id: 'LC-2026-0479', patient: 'Marcus Doan', vendor: 'Mountain Lab Services', item: 'Reline · upper denture', sent: '2026-04-25', eta: '2026-05-08', col: 'progress' },
  { id: 'LC-2026-0474', patient: 'Marcus Doan', vendor: 'Mountain Lab Services', item: 'Night guard · soft', sent: '2026-04-22', eta: '2026-05-04', col: 'progress' },
  { id: 'LC-2026-0469', patient: 'Priya Khanna', vendor: 'Pinnacle Dental Lab', item: 'Crown · #36', sent: '2026-04-15', eta: '2026-05-04', col: 'returned' },
  { id: 'LC-2026-0467', patient: 'Eli Brouwer', vendor: 'Apex Ortho Lab', item: 'Retainer · upper', sent: '2026-04-12', eta: '2026-05-04', col: 'returned' },
  { id: 'LC-2026-0463', patient: 'Daniel Okafor', vendor: 'Crown City Lab', item: 'Onlay · #14', sent: '2026-04-08', eta: '2026-05-02', col: 'returned' },
  { id: 'LC-2026-0455', patient: 'Yuki Tanaka', vendor: 'Pinnacle Dental Lab', item: 'Bridge · #14–#16', sent: '2026-04-01', eta: '2026-04-29', col: 'overdue' },
];

const VENDORS = [
  { name: 'Pinnacle Dental Lab', city: 'Calgary, AB', active: 9, on_time: '94%', avg_days: '8.2', focus: 'Crowns · bridges · onlays' },
  { name: 'Crown City Lab', city: 'Edmonton, AB', active: 4, on_time: '88%', avg_days: '11.0', focus: 'Implant restorations' },
  { name: 'Mountain Lab Services', city: 'Calgary, AB', active: 3, on_time: '96%', avg_days: '6.1', focus: 'Removables · relines' },
  { name: 'Apex Ortho Lab', city: 'Vancouver, BC', active: 2, on_time: '92%', avg_days: '9.4', focus: 'Retainers · aligners' },
];

const FILTERS = ['All', 'Sent', 'In progress', 'Returned', 'Overdue'];
const VENDOR_OPTIONS = VENDORS.map(v => v.name);
const COL_OPTIONS: { id: Col; label: string }[] = [
  { id: 'sent', label: 'Sent · waiting' },
  { id: 'progress', label: 'In progress' },
  { id: 'returned', label: 'Returned' },
  { id: 'overdue', label: 'Overdue' },
];
const colLabel: Record<Col, string> = { sent: 'Sent · waiting', progress: 'In progress', returned: 'Returned', overdue: 'Overdue' };

export default function LabPage() {
  const { addToast } = useToast();
  const [cases, setCases] = React.useState<LabCaseRow[]>(SEED_CASES);
  const [filter, setFilter] = React.useState('All');
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const [editing, setEditing] = React.useState(false);
  const [draft, setDraft] = React.useState<LabCaseRow | null>(null);

  const detailCase = detailId ? cases.find(c => c.id === detailId) ?? null : null;

  const filtered = cases.filter(c => {
    if (filter === 'All') return true;
    if (filter === 'Sent') return c.col === 'sent';
    if (filter === 'In progress') return c.col === 'progress';
    if (filter === 'Returned') return c.col === 'returned';
    if (filter === 'Overdue') return c.col === 'overdue';
    return true;
  });

  const startEdit = () => {
    if (!detailCase) return;
    setDraft({ ...detailCase });
    setEditing(true);
  };

  const saveEdit = () => {
    if (!draft) return;
    setCases(prev => prev.map(c => (c.id === draft.id ? draft : c)));
    addToast(`${draft.id} updated.`, draft.id);
    setEditing(false);
    setDraft(null);
  };

  const cancelEdit = () => {
    setEditing(false);
    setDraft(null);
  };

  const closeDetail = () => {
    setDetailId(null);
    setEditing(false);
    setDraft(null);
  };

  // LabPipeline expects LabCase shape (id, patient, vendor, item, eta, col with sent|progress|returned).
  // We pass through cases excluding 'overdue' for the kanban.
  const pipelineCases: LabCase[] = cases
    .filter(c => c.col !== 'overdue')
    .map(c => ({ id: c.id, patient: c.patient, vendor: c.vendor, item: c.item, eta: c.eta, col: c.col as 'sent' | 'progress' | 'returned' }));

  return (
    <>
      <style>{`
        .pill-sent{background:#FDF3E5;color:#B45309}.pill-progress{background:#D9EAF5;color:#2E6494}.pill-returned{background:#E8F5EE;color:#2A7D4F}.pill-overdue{background:#F8E5E8;color:#9B2335}
        .vendor-card{border:1px solid var(--rr-parchment);border-radius:6px;padding:16px 18px;display:flex;flex-direction:column;gap:8px}
        .vendor-name{font-family:var(--font-display);font-weight:700;font-size:.95rem;color:var(--rr-navy-800)}
        .vendor-meta{font-family:var(--font-ui);font-size:.74rem;color:var(--rr-slate-dark)}
        .vendor-stats{display:flex;gap:16px;margin-top:6px}.vendor-stat-k{font-family:var(--font-mono);font-size:.9rem;color:#0A192F;font-weight:600}.vendor-stat-v{font-family:var(--font-ui);font-size:.68rem;color:var(--rr-slate-dark);letter-spacing:.04em;text-transform:uppercase}
        .timeline-row{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--rr-parchment)}.timeline-row:last-child{border:none}.ts-dot{width:10px;height:10px;border-radius:999px;flex-shrink:0}
        table.cases{width:100%;border-collapse:collapse;font-family:var(--font-ui);font-size:.85rem}table.cases th{text-align:left;padding:12px 14px;color:var(--rr-slate-dark);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;border-bottom:1px solid var(--rr-parchment);font-weight:600}table.cases td{padding:14px;border-bottom:1px solid var(--rr-parchment);vertical-align:middle}table.cases tr:last-child td{border-bottom:none}table.cases tr:hover td{background:rgba(58,127,189,0.03)}
      `}</style>

      <div className="page-header">
        <div><h1 className="page-title">Lab pipeline</h1><div className="page-sub">{cases.length} cases in flight · {cases.filter(c => c.col === 'returned').length} ready · {cases.filter(c => c.col === 'overdue').length} overdue · 4 vendors</div></div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost btn-md" onClick={() => addToast('Pipeline exported.')}>Export pipeline</button>
          <button className="btn btn-primary btn-md" onClick={() => setDrawerOpen(true)}>+ New lab case</button>
        </div>
      </div>

      <div className="kpi-row">
        <KpiTile label="In flight" value="18" delta="+ 3" trend="up" accent="steel" />
        <KpiTile label="Returned · ready" value="3" delta="– 1" trend="up" accent="steel" />
        <KpiTile label="Overdue" value="1" delta="+ 1" trend="down" accent="navy" />
        <KpiTile label="On-time rate" value="93%" delta="+ 2.1%" trend="up" accent="steel" />
      </div>

      <div className="panel">
        <div className="panel-header"><div><div className="panel-h-title">Pipeline · Kanban</div><div className="panel-h-sub">Drag-style status flow · sent → in progress → returned</div></div><span className="panel-h-action">Switch to list ↓</span></div>
        <LabPipeline cases={pipelineCases} onCaseClick={(c: LabCase) => setDetailId(c.id)} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 18, alignItems: 'flex-start' }}>
        <div className="panel">
          <div className="panel-header">
            <div><div className="panel-h-title">All lab cases</div><div className="panel-h-sub">Showing {filtered.length} of {cases.length}</div></div>
            <div className="toolbar">{FILTERS.map(f => (<button key={f} className={'filter-pill' + (filter === f ? ' active' : '')} onClick={() => setFilter(f)}>{f}</button>))}</div>
          </div>
          <table className="cases">
            <thead><tr><th>Case</th><th>Patient</th><th>Item</th><th>Vendor</th><th>Sent</th><th>ETA</th><th>Status</th></tr></thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} style={{ cursor: 'pointer' }} onClick={() => { setDetailId(c.id); setEditing(false); }}>
                  <td className="id-cell">{c.id}</td><td style={{ fontWeight: 600, color: '#1C2333' }}>{c.patient}</td><td>{c.item}</td><td style={{ color: '#4A5568' }}>{c.vendor}</td>
                  <td className="id-cell">{c.sent}</td><td className="id-cell" style={{ color: c.col === 'overdue' ? '#9B2335' : '#1C2333' }}>{c.eta}</td>
                  <td><StatusPill status={c.col === 'progress' ? 'progress' : c.col} label={colLabel[c.col]} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="panel">
            <div className="panel-header"><div><div className="panel-h-title">Recent activity</div><div className="panel-h-sub">Pipeline events · last 24h</div></div></div>
            <div>
              {[{ dot: '#2A7D4F', t: '08:42', ev: 'Pinnacle Dental Lab returned', tail: 'LC-2026-0469 · Crown #36 · Priya Khanna' },
              { dot: '#3A7FBD', t: '08:14', ev: 'Crown City Lab acknowledged', tail: 'LC-2026-0463 · Onlay #14 · Daniel Okafor' },
              { dot: '#B45309', t: 'Yest', ev: 'Mountain Lab Services in progress', tail: 'LC-2026-0479 · Reline upper · Marcus Doan' },
              { dot: '#9B2335', t: 'Yest', ev: 'Bridge marked overdue', tail: 'LC-2026-0455 · Bridge #14–#16 · Yuki Tanaka' },
              { dot: '#3A7FBD', t: '2 d', ev: 'Apex Ortho Lab shipped', tail: 'LC-2026-0467 · Retainer · Eli Brouwer' },
              ].map((e, i) => (
                <div key={i} className="timeline-row"><span className="ts-dot" style={{ background: e.dot }} /><span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.72rem', color: '#8A9BB0', width: 42 }}>{e.t}</span><div style={{ display: 'flex', flexDirection: 'column' }}><span style={{ fontFamily: "'Inter', sans-serif", fontSize: '.84rem', color: '#1C2333', fontWeight: 600 }}>{e.ev}</span><span style={{ fontFamily: "'Inter', sans-serif", fontSize: '.74rem', color: '#4A5568' }}>{e.tail}</span></div></div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header"><div><div className="panel-h-title">Vendors</div><div className="panel-h-sub">Active labs · on-time performance · turnaround</div></div><a className="panel-h-action" href="/settings">Manage vendors →</a></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {VENDORS.map(v => (
            <a key={v.name} href="/settings" className="vendor-card" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="vendor-name">{v.name}</div><div className="vendor-meta">{v.city} · {v.focus}</div>
              <div className="vendor-stats"><div><div className="vendor-stat-k">{v.active}</div><div className="vendor-stat-v">Active</div></div><div><div className="vendor-stat-k">{v.on_time}</div><div className="vendor-stat-v">On-time</div></div><div><div className="vendor-stat-k">{v.avg_days}</div><div className="vendor-stat-v">Avg days</div></div></div>
            </a>
          ))}
        </div>
      </div>

      <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>ROCKYRIDGE · DENTAL AI · v1</div>

      {/* New Lab Case Drawer */}
      {drawerOpen && (
        <Drawer open={true} onClose={() => setDrawerOpen(false)} meta="New case" title="Create lab case" sub="Send a new case to the lab."
          footer={<><button className="btn btn-ghost btn-md" onClick={() => setDrawerOpen(false)}>Cancel</button><button className="btn btn-primary btn-md" onClick={() => { setDrawerOpen(false); addToast('Lab case created.', 'LC-2026-XXXX'); }}>Send to lab</button></>}>
          <div className="field"><label className="lbl">Patient</label><select className="d-input" defaultValue="P-018342">{['Alice Stevens', 'Marcus Doan', 'Priya Khanna', 'Eli Brouwer', 'Sofía Castillo', 'Daniel Okafor'].map(n => <option key={n}>{n}</option>)}</select></div>
          <div className="field"><label className="lbl">Item type</label><select className="d-input" defaultValue="crown"><option>Crown</option><option>Bridge</option><option>Implant</option><option>Reline</option><option>Night guard</option><option>Retainer</option><option>Onlay</option></select></div>
          <div className="field"><label className="lbl">Vendor</label><select className="d-input" defaultValue="pinnacle"><option>Pinnacle Dental Lab</option><option>Crown City Lab</option><option>Mountain Lab Services</option><option>Apex Ortho Lab</option></select></div>
          <div className="field-row"><div className="field"><label className="lbl">Sent date</label><input className="d-input" type="date" defaultValue="2026-05-04" /></div><div className="field"><label className="lbl">ETA</label><input className="d-input" type="date" defaultValue="2026-05-18" /></div></div>
          <div className="field"><label className="lbl">Notes</label><textarea className="d-textarea" placeholder="Special instructions for the lab..." /></div>
        </Drawer>
      )}

      {/* Case Detail Modal — overview + inline edit */}
      {detailCase && (
        <CenterModal open={true} onClose={closeDetail} width="min(560px, 92vw)">
          <div className="center-modal-topbar"><button className="drawer-back" onClick={closeDetail}><ArrowLeft size={18} strokeWidth={1.5} /></button><span className="back-label">{editing ? 'Editing case' : 'Back to Lab Pipeline'}</span></div>
          <div className="center-modal-body">
            <div className="appt-ws-hero">
              <div className="appt-ws-ava">{detailCase.patient.split(' ').map(s => s[0]).join('').toUpperCase()}</div>
              <div className="appt-ws-info">
                <div className="appt-ws-name">{detailCase.patient}</div>
                <div className="appt-ws-detail">{(editing && draft ? draft.item : detailCase.item)}</div>
                <div className="appt-ws-id">{detailCase.id}</div>
              </div>
              <StatusPill status={(editing && draft ? draft.col : detailCase.col) === 'progress' ? 'progress' : (editing && draft ? draft.col : detailCase.col)} label={colLabel[(editing && draft ? draft.col : detailCase.col)]} />
            </div>

            {!editing && (
              <div>
                <div className="detail-row"><span className="detail-k">Case ID</span><span className="detail-v">{detailCase.id}</span></div>
                <div className="detail-row"><span className="detail-k">Item</span><span className="detail-v">{detailCase.item}</span></div>
                <div className="detail-row"><span className="detail-k">Vendor</span><span className="detail-v">{detailCase.vendor}</span></div>
                <div className="detail-row"><span className="detail-k">Sent</span><span className="detail-v">{detailCase.sent}</span></div>
                <div className="detail-row"><span className="detail-k">ETA</span><span className="detail-v">{detailCase.eta}</span></div>
                <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v">{colLabel[detailCase.col]}</span></div>
              </div>
            )}

            {editing && draft && (
              <div>
                <div className="field"><label className="lbl">Item</label><input className="d-input" value={draft.item} onChange={e => setDraft({ ...draft, item: e.target.value })} /></div>
                <div className="field"><label className="lbl">Vendor</label>
                  <select className="d-input" value={draft.vendor} onChange={e => setDraft({ ...draft, vendor: e.target.value })}>
                    {VENDOR_OPTIONS.map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </div>
                <div className="field-row">
                  <div className="field"><label className="lbl">Sent</label><input className="d-input" type="date" value={draft.sent} onChange={e => setDraft({ ...draft, sent: e.target.value })} /></div>
                  <div className="field"><label className="lbl">ETA</label><input className="d-input" type="date" value={draft.eta} onChange={e => setDraft({ ...draft, eta: e.target.value })} /></div>
                </div>
                <div className="field"><label className="lbl">Status</label>
                  <select className="d-input" value={draft.col} onChange={e => setDraft({ ...draft, col: e.target.value as Col })}>
                    {COL_OPTIONS.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
                  </select>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: 8 }}>
              {!editing && (
                <>
                  <button className="btn btn-primary btn-md" onClick={startEdit}>Edit case</button>
                  <button className="btn btn-ghost btn-md" onClick={closeDetail}>Close</button>
                </>
              )}
              {editing && (
                <>
                  <button className="btn btn-primary btn-md" onClick={saveEdit}>Save changes</button>
                  <button className="btn btn-ghost btn-md" onClick={cancelEdit}>Cancel</button>
                </>
              )}
            </div>
          </div>
        </CenterModal>
      )}
    </>
  );
}
