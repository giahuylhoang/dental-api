'use client';

import React, { useState } from 'react';
import { KpiTile } from '@/components/dental/KpiTile';

// TODO: wire to dental-agent — endpoint not yet implemented
const ALL_CASES = [
  { id: 'LC-2026-0481', patient: 'Alice Stevens',  vendor: 'Pinnacle Dental Lab',   item: 'Crown · #36',            sent: '2026-04-28', eta: '2026-05-12', status: 'sent'     },
  { id: 'LC-2026-0476', patient: 'Sofía Castillo', vendor: 'Crown City Lab',        item: 'Implant abutment · #11', sent: '2026-04-26', eta: '2026-05-18', status: 'sent'     },
  { id: 'LC-2026-0479', patient: 'Marcus Doan',    vendor: 'Mountain Lab Services', item: 'Reline · upper denture', sent: '2026-04-25', eta: '2026-05-08', status: 'progress' },
  { id: 'LC-2026-0474', patient: 'Marcus Doan',    vendor: 'Mountain Lab Services', item: 'Night guard · soft',     sent: '2026-04-22', eta: '2026-05-04', status: 'progress' },
  { id: 'LC-2026-0469', patient: 'Priya Khanna',   vendor: 'Pinnacle Dental Lab',   item: 'Crown · #36',            sent: '2026-04-15', eta: '2026-05-04', status: 'returned' },
  { id: 'LC-2026-0467', patient: 'Eli Brouwer',    vendor: 'Apex Ortho Lab',        item: 'Retainer · upper',       sent: '2026-04-12', eta: '2026-05-04', status: 'returned' },
  { id: 'LC-2026-0463', patient: 'Daniel Okafor',  vendor: 'Crown City Lab',        item: 'Onlay · #14',            sent: '2026-04-08', eta: '2026-05-02', status: 'returned' },
  { id: 'LC-2026-0455', patient: 'Yuki Tanaka',    vendor: 'Pinnacle Dental Lab',   item: 'Bridge · #14–#16',       sent: '2026-04-01', eta: '2026-04-29', status: 'overdue'  },
];

// TODO: wire to dental-agent — endpoint not yet implemented
const VENDORS = [
  { name: 'Pinnacle Dental Lab',   city: 'Calgary, AB',   active: 9, on_time: '94%', avg_days: '8.2',  focus: 'Crowns · bridges · onlays' },
  { name: 'Crown City Lab',        city: 'Edmonton, AB',  active: 4, on_time: '88%', avg_days: '11.0', focus: 'Implant restorations'      },
  { name: 'Mountain Lab Services', city: 'Calgary, AB',   active: 3, on_time: '96%', avg_days: '6.1',  focus: 'Removables · relines'      },
  { name: 'Apex Ortho Lab',        city: 'Vancouver, BC', active: 2, on_time: '92%', avg_days: '9.4',  focus: 'Retainers · aligners'       },
];

// TODO: wire to dental-agent — endpoint not yet implemented (LabPipeline stages)
const LAB_COLUMNS = [
  { id: 'sent',     label: 'Sent · waiting on lab'    },
  { id: 'progress', label: 'In progress'              },
  { id: 'returned', label: 'Returned · ready to seat' },
];

const LAB_PIPELINE_CASES = [
  { id: 'LC-2026-0481', patient: 'Alice Stevens',  vendor: 'Pinnacle Dental Lab',   item: 'Crown · #36',            eta: '2026-05-12', col: 'sent'     },
  { id: 'LC-2026-0476', patient: 'Sofía Castillo', vendor: 'Crown City Lab',        item: 'Implant · #11',          eta: '2026-05-18', col: 'sent'     },
  { id: 'LC-2026-0474', patient: 'Marcus Doan',    vendor: 'Mountain Lab Services', item: 'Reline · upper denture', eta: '2026-05-08', col: 'progress' },
  { id: 'LC-2026-0469', patient: 'Priya Khanna',   vendor: 'Pinnacle Dental Lab',   item: 'Crown · #36',            eta: '2026-05-04', col: 'returned' },
  { id: 'LC-2026-0467', patient: 'Eli Brouwer',    vendor: 'Apex Ortho Lab',        item: 'Retainer',               eta: '2026-05-04', col: 'returned' },
];

const STATUS_PILL: Record<string, string> = {
  sent:     'pill pill-sent',
  progress: 'pill pill-progress',
  returned: 'pill pill-returned',
  overdue:  'pill pill-overdue',
};

const STATUS_LABEL: Record<string, string> = {
  sent:     'Sent · waiting',
  progress: 'In progress',
  returned: 'Returned',
  overdue:  'Overdue',
};

const FILTERS = ['All', 'Sent', 'In progress', 'Returned', 'Overdue'];

const TIMELINE = [
  { dot: '#2A7D4F', t: '08:42', ev: 'Pinnacle Dental Lab returned',     tail: 'LC-2026-0469 · Crown #36 · Priya Khanna'         },
  { dot: '#3A7FBD', t: '08:14', ev: 'Crown City Lab acknowledged',      tail: 'LC-2026-0463 · Onlay #14 · Daniel Okafor'        },
  { dot: '#B45309', t: 'Yest',  ev: 'Mountain Lab Services in progress',tail: 'LC-2026-0479 · Reline upper · Marcus Doan'        },
  { dot: '#9B2335', t: 'Yest',  ev: 'Bridge marked overdue',            tail: 'LC-2026-0455 · Bridge #14–#16 · Yuki Tanaka'     },
  { dot: '#3A7FBD', t: '2 d',   ev: 'Apex Ortho Lab shipped',           tail: 'LC-2026-0467 · Retainer · Eli Brouwer'           },
];

function LabPipeline() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
      {LAB_COLUMNS.map(col => {
        const cards = LAB_PIPELINE_CASES.filter(c => c.col === col.id);
        return (
          <div key={col.id} style={{ background: '#FAF9F6', border: '1px solid #EDE9E0', borderRadius: 6, padding: 12, display: 'flex', flexDirection: 'column', gap: 8, minHeight: 240 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 6px 8px' }}>
              <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#4A5568' }}>{col.label}</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#3A7FBD', fontWeight: 600, padding: '1px 8px', background: '#D9EAF5', borderRadius: 999 }}>{cards.length}</span>
            </div>
            {cards.map(c => (
              <div key={c.id} style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 6, boxShadow: '0 1px 2px rgba(10,25,47,0.04)', cursor: 'pointer' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                  <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.85rem', color: '#1C2333' }}>{c.patient}</div>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.66rem', color: '#8A9BB0' }}>{c.id}</span>
                </div>
                <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: '#3D4D61' }}>{c.item}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                  <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.7rem', color: '#4A5568' }}>{c.vendor}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#B45309' }}>ETA {c.eta}</span>
                </div>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}

export default function LabPage() {
  const [filter, setFilter] = useState('All');
  const [toasts, setToasts] = useState<{ id: number; msg: string }[]>([]);

  const addToast = (msg: string) => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3000);
  };

  const filtered = ALL_CASES.filter(c => {
    if (filter === 'All') return true;
    if (filter === 'Sent') return c.status === 'sent';
    if (filter === 'In progress') return c.status === 'progress';
    if (filter === 'Returned') return c.status === 'returned';
    if (filter === 'Overdue') return c.status === 'overdue';
    return true;
  });

  return (
    <>
      <div style={{ padding: '28px 32px', display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 1280, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>

        {/* Page header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontWeight: 800, fontSize: '1.8rem', color: 'var(--rr-navy-800)', letterSpacing: '-.025em', margin: '0 0 4px' }}>Lab pipeline</h1>
            <div style={{ fontSize: '.88rem', color: 'var(--rr-slate-dark)' }}>{ALL_CASES.length} cases in flight · 3 ready to seat · 1 overdue · 4 vendors active</div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-ghost btn-md" onClick={() => addToast('Pipeline exported — lab_pipeline_2026-05-03.csv')}>Export pipeline</button>
            <button className="btn btn-primary btn-md" onClick={() => addToast('New lab case drawer would open here.')}>+ New lab case</button>
          </div>
        </div>

        {/* KPI strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
          <KpiTile label="In flight"        value="18"  delta="+ 3"    trend="up"   accent="steel" />
          <KpiTile label="Returned · ready" value="3"   delta="– 1"    trend="up"   accent="steel" />
          <KpiTile label="Overdue"          value="1"   delta="+ 1"    trend="down" accent="navy"  />
          <KpiTile label="On-time rate"     value="93%" delta="+ 2.1%" trend="up"   accent="steel" />
        </div>

        {/* LabPipeline panel */}
        <div style={{ background: '#fff', border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)' }}>Pipeline · Kanban</div>
              <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark)', marginTop: 2 }}>Drag-style status flow · sent → in progress → returned</div>
            </div>
            <span style={{ fontSize: '.82rem', color: 'hsl(var(--primary))', cursor: 'pointer' }}>Switch to list →</span>
          </div>
          <LabPipeline />
        </div>

        {/* Cases table + Recent activity */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 18, alignItems: 'flex-start' }}>
          <div style={{ background: '#fff', border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)' }}>All lab cases</div>
                <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark)', marginTop: 2 }}>Showing {filtered.length} of {ALL_CASES.length}</div>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                {FILTERS.map(f => (
                  <button key={f} onClick={() => setFilter(f)} style={{
                    display: 'inline-flex', alignItems: 'center', height: 32, padding: '0 12px', borderRadius: 999,
                    border: `1px solid ${filter === f ? 'var(--rr-steel-200)' : 'var(--rr-parchment)'}`,
                    background: filter === f ? 'var(--rr-mist)' : '#fff',
                    color: filter === f ? 'var(--rr-navy-800)' : 'var(--rr-slate-dark)',
                    fontWeight: filter === f ? 600 : 400,
                    fontSize: '.76rem', cursor: 'pointer',
                  }}>{f}</button>
                ))}
              </div>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '.85rem' }}>
              <thead>
                <tr>
                  {['Case', 'Patient', 'Item', 'Vendor', 'Sent', 'ETA', 'Status'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '12px 14px', color: 'var(--rr-slate-dark)', fontSize: '.68rem', letterSpacing: '.08em', textTransform: 'uppercase', borderBottom: '1px solid var(--rr-parchment)', fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(c => (
                  <tr key={c.id} style={{ cursor: 'pointer' }}>
                    <td style={{ padding: 14, borderBottom: '1px solid var(--rr-parchment)', fontFamily: "'JetBrains Mono', monospace", fontSize: '.76rem', color: 'var(--rr-slate-dark)' }}>{c.id}</td>
                    <td style={{ padding: 14, borderBottom: '1px solid var(--rr-parchment)', fontWeight: 600, color: '#1C2333' }}>{c.patient}</td>
                    <td style={{ padding: 14, borderBottom: '1px solid var(--rr-parchment)' }}>{c.item}</td>
                    <td style={{ padding: 14, borderBottom: '1px solid var(--rr-parchment)', color: '#4A5568' }}>{c.vendor}</td>
                    <td style={{ padding: 14, borderBottom: '1px solid var(--rr-parchment)', fontFamily: "'JetBrains Mono', monospace", fontSize: '.76rem', color: 'var(--rr-slate-dark)' }}>{c.sent}</td>
                    <td style={{ padding: 14, borderBottom: '1px solid var(--rr-parchment)', fontFamily: "'JetBrains Mono', monospace", fontSize: '.76rem', color: c.status === 'overdue' ? '#9B2335' : '#1C2333' }}>{c.eta}</td>
                    <td style={{ padding: 14, borderBottom: '1px solid var(--rr-parchment)' }}>
                      <span style={{
                        fontSize: '.66rem', fontWeight: 600, padding: '3px 10px', borderRadius: 999, letterSpacing: '.06em', textTransform: 'uppercase', display: 'inline-block',
                        background: c.status === 'sent' ? '#FDF3E5' : c.status === 'progress' ? '#D9EAF5' : c.status === 'returned' ? '#E8F5EE' : '#F8E5E8',
                        color: c.status === 'sent' ? '#B45309' : c.status === 'progress' ? '#2E6494' : c.status === 'returned' ? '#2A7D4F' : '#9B2335',
                      }}>{STATUS_LABEL[c.status]}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Recent activity */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ background: '#fff', border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)' }}>Recent activity</div>
                  <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark)', marginTop: 2 }}>Pipeline events · last 24h</div>
                </div>
              </div>
              {TIMELINE.map((e, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: i < TIMELINE.length - 1 ? '1px solid var(--rr-parchment)' : 'none' }}>
                  <span style={{ width: 10, height: 10, borderRadius: 999, flexShrink: 0, background: e.dot, display: 'inline-block' }} />
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.72rem', color: '#8A9BB0', width: 42 }}>{e.t}</span>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '.84rem', color: '#1C2333', fontWeight: 600 }}>{e.ev}</span>
                    <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '.74rem', color: '#4A5568' }}>{e.tail}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Vendor cards panel */}
        <div style={{ background: '#fff', border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: '22px 24px', boxShadow: 'var(--shadow-xs)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)' }}>Vendors</div>
              <div style={{ fontSize: '.72rem', color: 'var(--rr-slate-dark)', marginTop: 2 }}>Active labs · on-time performance · turnaround</div>
            </div>
            <span style={{ fontSize: '.82rem', color: 'hsl(var(--primary))', cursor: 'pointer' }}>Manage vendors →</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {VENDORS.map(v => (
              <div key={v.name} style={{ border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ fontWeight: 700, fontSize: '.95rem', color: 'var(--rr-navy-800)' }}>{v.name}</div>
                <div style={{ fontSize: '.74rem', color: 'var(--rr-slate-dark)' }}>{v.city} · {v.focus}</div>
                <div style={{ display: 'flex', gap: 16, marginTop: 6 }}>
                  <div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.9rem', color: '#0A192F', fontWeight: 600 }}>{v.active}</div>
                    <div style={{ fontSize: '.68rem', color: 'var(--rr-slate-dark)', letterSpacing: '.04em', textTransform: 'uppercase' }}>Active cases</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.9rem', color: '#0A192F', fontWeight: 600 }}>{v.on_time}</div>
                    <div style={{ fontSize: '.68rem', color: 'var(--rr-slate-dark)', letterSpacing: '.04em', textTransform: 'uppercase' }}>On-time</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.9rem', color: '#0A192F', fontWeight: 600 }}>{v.avg_days}</div>
                    <div style={{ fontSize: '.68rem', color: 'var(--rr-slate-dark)', letterSpacing: '.04em', textTransform: 'uppercase' }}>Avg days</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {toasts.length > 0 && (
        <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 100, display: 'flex', flexDirection: 'column', gap: 8, pointerEvents: 'none' }}>
          {toasts.map(t => (
            <div key={t.id} style={{ background: 'var(--rr-navy-800)', color: 'var(--rr-warm-white)', padding: '12px 18px', borderRadius: 6, fontSize: '.85rem', boxShadow: '0 4px 16px rgba(10,25,47,0.22)', pointerEvents: 'auto', maxWidth: 380 }}>{t.msg}</div>
          ))}
        </div>
      )}
    </>
  );
}
