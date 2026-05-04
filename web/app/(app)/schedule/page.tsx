'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '@/lib/api/client';

// TODO: wire to dental-agent — endpoint not yet implemented
const OPS = ['Op 1', 'Op 2', 'Op 3', 'Op 4'];

const HOURS = [
  '08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30',
  '12:00','12:30','13:00','13:30','14:00','14:30','15:00','15:30',
  '16:00','16:30','17:00',
];

const PROVIDERS_SEED = [
  { id: '1', name: 'Dr Hau Le',   color: '#3A7FBD', bg: '#D9EAF5' },
  { id: '2', name: 'Dr Sara Lim', color: '#2E6494', bg: '#A8CCE8' },
  { id: '3', name: 'Hyg. Renu',   color: '#B45309', bg: '#FDF3E5' },
];

const STATUS_BG: Record<string, { bg: string; border: string; fg: string }> = {
  confirmed: { bg: '#D9EAF5', border: '#3A7FBD', fg: '#0A192F' },
  pending:   { bg: '#FDF3E5', border: '#B45309', fg: '#7C3F0A' },
  no_show:   { bg: '#F8E5E8', border: '#9B2335', fg: '#5C1620' },
  completed: { bg: '#F5F2EC', border: '#8A9BB0', fg: '#4A5568' },
};

interface Appointment {
  id: string;
  patient: string;
  time: string;
  duration: number;
  chair: string;
  status: string;
  provider: string;
  kind: string;
}

interface Provider {
  id: string;
  name: string;
  color?: string;
  bg?: string;
}

const OPEN_SLOTS = [
  { t: '11:30', op: 'Op 2', dur: '30m' },
  { t: '12:00', op: 'Op 3', dur: '60m' },
  { t: '12:30', op: 'Op 1', dur: '30m' },
  { t: '13:00', op: 'Op 4', dur: '90m' },
];

const WAITLIST = [
  { name: 'Rae Tomlinson', reason: 'Crown seat' },
  { name: 'Dimitri Voss',  reason: 'Hygiene'    },
  { name: 'Yuki Tanaka',   reason: 'Recall'      },
];

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function nowTime() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

function nowRowOffset() {
  const d = new Date();
  const mins = d.getHours() * 60 + d.getMinutes();
  const startMins = 8 * 60;
  return Math.max(0, mins - startMins);
}

export default function SchedulePage() {
  const [activeDay, setActiveDay] = useState('Sat');
  const [selectedProvider, setSelectedProvider] = useState('all');
  const [toasts, setToasts] = useState<{ id: number; msg: string }[]>([]);
  const [currentDate, setCurrentDate] = useState('May 4 · Saturday');
  const [nowOffset, setNowOffset] = useState(nowRowOffset());

  const addToast = (msg: string) => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3000);
  };

  useEffect(() => {
    const iv = setInterval(() => setNowOffset(nowRowOffset()), 60000);
    return () => clearInterval(iv);
  }, []);

  const { data: appointments = [] } = useQuery<Appointment[]>({
    queryKey: ['appointments', todayStr()],
    queryFn: () => fetcher<Appointment[]>(`/api/appointments?date=${todayStr()}`),
  });

  const { data: providersData = [] } = useQuery<Provider[]>({
    queryKey: ['providers'],
    queryFn: () => fetcher<Provider[]>('/api/providers'),
  });

  const providers = providersData.length > 0
    ? providersData.map((p, i) => ({
        ...p,
        color: PROVIDERS_SEED[i]?.color ?? '#3A7FBD',
        bg:    PROVIDERS_SEED[i]?.bg    ?? '#D9EAF5',
      }))
    : PROVIDERS_SEED;

  const filteredAppts = selectedProvider === 'all'
    ? appointments
    : appointments.filter(a => a.provider.startsWith(
        providers.find(p => p.id === selectedProvider)?.name.split(' ')[0] ?? ''
      ));

  // "now" line row: each row = 36px, offset from 08:00
  const nowTop = nowOffset * (36 / 30); // px per minute

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 18, padding: '24px 28px', maxWidth: 1280, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        {/* Page header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <h1 style={{ fontWeight: 800, fontSize: '1.8rem', color: 'var(--rr-navy-800, #0A192F)', letterSpacing: '-.025em', margin: '0 0 4px' }}>Schedule</h1>
            <div style={{ fontSize: '.88rem', color: 'var(--rr-slate-dark, #4A5568)' }}>
              {currentDate} · {appointments.length} appointments
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-ghost btn-md" onClick={() => addToast('Jumped to today.')}>Today</button>
            <button className="btn btn-ghost btn-md" onClick={() => addToast('Day schedule printed.')}>Print day</button>
            <button className="btn btn-primary btn-md" onClick={() => addToast('Booking drawer would open here.')}>+ Book appointment</button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 18, alignItems: 'flex-start' }}>
          {/* Main grid panel */}
          <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, boxShadow: '0 1px 3px rgba(10,25,47,0.06)' }}>
            {/* Day toolbar */}
            <div className="day-toolbar" style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '14px 18px', borderBottom: '1px solid #EDE9E0' }}>
              <button className="nav-btn" style={{ width: 32, height: 32, borderRadius: 4, border: '1px solid #EDE9E0', background: '#fff', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#4A5568' }}>‹</button>
              <span style={{ fontWeight: 700, fontSize: '1rem', color: '#0A192F', margin: '0 6px' }}>May 4 · Saturday</span>
              <button className="nav-btn" style={{ width: 32, height: 32, borderRadius: 4, border: '1px solid #EDE9E0', background: '#fff', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#4A5568' }}>›</button>
              <div style={{ display: 'inline-flex', gap: 6, marginLeft: 14 }}>
                {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(d => (
                  <button
                    key={d}
                    onClick={() => setActiveDay(d)}
                    style={{
                      height: 32, padding: '0 12px', borderRadius: 4,
                      border: `1px solid ${d === activeDay ? '#0A192F' : '#EDE9E0'}`,
                      background: d === activeDay ? '#0A192F' : '#fff',
                      cursor: 'pointer', fontSize: '.78rem',
                      color: d === activeDay ? '#fff' : '#4A5568',
                      fontWeight: d === activeDay ? 600 : 400,
                    }}
                  >{d}</button>
                ))}
              </div>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: '.74rem', color: '#4A5568' }}>Provider</span>
                <select
                  value={selectedProvider}
                  onChange={e => setSelectedProvider(e.target.value)}
                  style={{ height: 32, borderRadius: 4, border: '1px solid #EDE9E0', padding: '0 10px', fontSize: '.78rem', color: '#1C2333', background: '#fff' }}
                >
                  <option value="all">All providers</option>
                  {providers.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
            </div>

            {/* Schedule grid */}
            <div style={{ padding: '14px 18px 22px' }}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '64px repeat(4, 1fr)',
                  gap: 1,
                  background: '#EDE9E0',
                  border: '1px solid #EDE9E0',
                  borderRadius: 4,
                  overflow: 'hidden',
                }}
              >
                {/* Column headers */}
                <div style={{ background: '#FAF8F5', padding: '10px 12px', fontSize: '.72rem', fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: '#4A5568' }}>Time</div>
                {OPS.map(o => (
                  <div key={o} style={{ background: '#FAF8F5', padding: '10px 12px', fontSize: '.72rem', fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: '#4A5568' }}>{o}</div>
                ))}

                {/* Time rows */}
                {HOURS.map((h, hi) => (
                  <React.Fragment key={h}>
                    <div style={{ background: '#FAF8F5', padding: '4px 10px', fontSize: '.7rem', color: '#4A5568', display: 'flex', alignItems: 'flex-start', fontFamily: 'monospace' }}>{h}</div>
                    {OPS.map((op, oi) => {
                      const chair = String(oi + 1);
                      const appts = filteredAppts.filter(a => a.chair === chair && a.time === h);
                      const isNowRow = hi === Math.floor(nowOffset / 30);
                      return (
                        <div key={`${op}-${h}`} style={{ background: '#fff', minHeight: 36, padding: '4px 6px', position: 'relative' }}>
                          {appts.map(a => {
                            const rows = Math.max(1, Math.round(a.duration / 30));
                            const tone = STATUS_BG[a.status] ?? STATUS_BG.confirmed;
                            const prov = providers.find(p => a.provider.startsWith(p.name.split(' ')[0])) ?? providers[0];
                            return (
                              <div
                                key={a.id}
                                style={{
                                  position: 'absolute', left: 4, right: 4,
                                  top: 4, height: rows * 36 - 8,
                                  borderRadius: 4, padding: '6px 8px',
                                  boxShadow: '0 1px 2px rgba(10,25,47,0.08)',
                                  cursor: 'pointer', overflow: 'hidden',
                                  background: tone.bg,
                                  border: `1px solid ${tone.border}`,
                                  borderLeft: `3px solid ${prov?.color ?? '#3A7FBD'}`,
                                  color: tone.fg,
                                  textDecoration: 'none', display: 'block',
                                }}
                              >
                                <div style={{ fontFamily: 'monospace', fontSize: '.68rem', opacity: .8 }}>{a.time} · {a.duration}m</div>
                                <div style={{ fontWeight: 600, fontSize: '.82rem', lineHeight: 1.2, marginTop: 2 }}>{a.patient}</div>
                                <div style={{ fontSize: '.72rem', opacity: .82, marginTop: 2 }}>{a.kind}</div>
                              </div>
                            );
                          })}
                          {isNowRow && oi === 0 && (
                            <div style={{
                              position: 'absolute', left: 0, right: 0,
                              top: (nowOffset % 30) * (36 / 30),
                              height: 2, background: '#9B2335', zIndex: 5,
                            }}>
                              <div style={{ position: 'absolute', left: -5, top: -3, width: 8, height: 8, borderRadius: 999, background: '#9B2335' }} />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </React.Fragment>
                ))}
              </div>
            </div>

            {/* Legend */}
            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', padding: '14px 18px', borderTop: '1px solid #EDE9E0', fontSize: '.74rem', color: '#4A5568' }}>
              {[
                { label: 'Confirmed', bg: '#D9EAF5', border: '#3A7FBD' },
                { label: 'Pending',   bg: '#FDF3E5', border: '#B45309' },
                { label: 'No-show',   bg: '#F8E5E8', border: '#9B2335' },
                { label: 'Completed', bg: '#F5F2EC', border: '#8A9BB0' },
              ].map(s => (
                <span key={s.label}>
                  <span style={{ width: 12, height: 12, borderRadius: 3, display: 'inline-block', marginRight: 6, verticalAlign: 'middle', background: s.bg, border: `1px solid ${s.border}` }} />
                  {s.label}
                </span>
              ))}
              <span style={{ marginLeft: 'auto', color: '#9B2335', fontWeight: 600 }}>● Now · {nowTime()}</span>
            </div>
          </div>

          {/* Side panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Providers today */}
            <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, boxShadow: '0 1px 3px rgba(10,25,47,0.06)', padding: '18px 20px' }}>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0A192F', marginBottom: 4 }}>Providers today</div>
              <div style={{ fontSize: '.72rem', color: '#4A5568', marginBottom: 14 }}>Working hours · current load</div>
              {providers.map(p => {
                const load = appointments.filter(a => a.provider.startsWith(p.name.split(' ')[0])).length;
                return (
                  <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #EDE9E0', fontSize: '.82rem', color: '#1C2333' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ width: 10, height: 10, borderRadius: 999, background: p.color }} />
                      {p.name}
                    </span>
                    <span style={{ fontFamily: 'monospace', fontSize: '.78rem', color: '#1C2333' }}>{load} appts</span>
                  </div>
                );
              })}
            </div>

            {/* Open slots */}
            <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, boxShadow: '0 1px 3px rgba(10,25,47,0.06)', padding: '18px 20px' }}>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0A192F', marginBottom: 4 }}>Open slots</div>
              <div style={{ fontSize: '.72rem', color: '#4A5568', marginBottom: 14 }}>Next 90 minutes · book in one click</div>
              {OPEN_SLOTS.map(s => (
                <div key={s.t + s.op} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #EDE9E0', fontSize: '.82rem', color: '#1C2333' }}>
                  <span>
                    <span style={{ fontFamily: 'monospace', color: '#0A192F', fontWeight: 600 }}>{s.t}</span>
                    <span style={{ marginLeft: 10, color: '#4A5568' }}>{s.op} · {s.dur}</span>
                  </span>
                  <button className="btn btn-ghost btn-sm" onClick={() => addToast(`Booking started for ${s.op} at ${s.t}.`)}>Book</button>
                </div>
              ))}
            </div>

            {/* Waitlist */}
            <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, boxShadow: '0 1px 3px rgba(10,25,47,0.06)', padding: '18px 20px' }}>
              <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0A192F', marginBottom: 4 }}>Waitlist</div>
              <div style={{ fontSize: '.72rem', color: '#4A5568', marginBottom: 14 }}>Patients ready for a sooner slot</div>
              {WAITLIST.map(w => (
                <div key={w.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #EDE9E0', fontSize: '.82rem', color: '#1C2333' }}>
                  <span>{w.name}<span style={{ color: '#8A9BB0', marginLeft: 8, fontSize: '.72rem' }}>{w.reason}</span></span>
                  <button className="btn btn-ghost btn-sm" onClick={() => addToast(`Slot offered to ${w.name}.`)}>Offer</button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', padding: '20px 0', fontSize: '.72rem', color: 'var(--rr-slate, #8A9BB0)', letterSpacing: '.06em' }}>
          ROCKYRIDGE · DENTAL AI · v1
        </div>
      </div>

      {/* Toast container */}
      {toasts.length > 0 && (
        <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 100, display: 'flex', flexDirection: 'column', gap: 8, pointerEvents: 'none' }}>
          {toasts.map(t => (
            <div key={t.id} style={{ background: '#0A192F', color: '#FAF8F5', padding: '12px 18px', borderRadius: 6, fontSize: '.85rem', boxShadow: '0 4px 16px rgba(10,25,47,0.22)', pointerEvents: 'auto', maxWidth: 380 }}>
              {t.msg}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
