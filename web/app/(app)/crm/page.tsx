'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '@/lib/api/client';
import { KpiTile } from '@/components/dental/KpiTile';
import { StatusPill } from '@/components/dental/StatusPill';
import styles from './page.module.css';

// TODO: wire to dental-agent — endpoint not yet implemented (activities seed)
const SEED_ACTIVITIES = [
  { id: 'a1', kind: 'sms',     icon: 'sms',     author: 'Kim Sato',      when: 'Today 10:14',  body: 'Sent confirmation SMS for Saturday 10:30 consult — replied with thumbs-up.' },
  { id: 'a2', kind: 'note',    icon: 'note',    author: 'Hau Le',        when: 'Today 09:42',  body: 'Quoted $4,200 for upper Invisalign incl. retainers. Patient considering.' },
  { id: 'a3', kind: 'call',    icon: 'call',    author: 'Kim Sato',      when: 'Yesterday',    body: '14-minute discovery call. Coverage clarified · Manulife covers 60% to $1,500 cap.' },
  { id: 'a4', kind: 'email',   icon: 'email',   author: 'Auto · system', when: '2 days ago',   body: 'Welcome packet sent · pricing PDF attached.' },
  { id: 'a5', kind: 'meeting', icon: 'meeting', author: 'Hau Le',        when: '3 days ago',   body: 'In-clinic exam · panoramic taken · referred to ortho consult before treatment plan.' },
];

// TODO: wire to dental-agent — endpoint not yet implemented (source breakdown)
const SEED_SOURCES = [
  { name: 'Google',    leads: 28, conv_rate: 22 },
  { name: 'Referral',  leads: 19, conv_rate: 47 },
  { name: 'Instagram', leads: 11, conv_rate: 18 },
  { name: 'Walk-in',   leads:  7, conv_rate: 36 },
  { name: 'Other',     leads:  3, conv_rate:  0 },
];

// TODO: wire to dental-agent — endpoint not yet implemented (tasks)
const SEED_TASKS = [
  { time: 'Today',    who: 'Rae Tomlinson',  what: 'Send Invisalign quote PDF',      kind: 'email' },
  { time: 'Today',    who: 'Tom Brennan',    what: 'Follow-up call · voicemail',     kind: 'call' },
  { time: 'Tomorrow', who: 'Hana Park',      what: 'Check Sun Life pre-auth status', kind: 'note' },
  { time: 'May 6',    who: 'Joaquin Ramos',  what: 'Confirm Saturday booking',       kind: 'sms' },
];

const COLUMNS = [
  { id: 'NEW',       label: 'New',       dot: '#8A9BB0' },
  { id: 'CONTACTED', label: 'Contacted', dot: '#3A7FBD' },
  { id: 'QUALIFIED', label: 'Qualified', dot: '#B45309' },
  { id: 'CONVERTED', label: 'Converted', dot: '#2A7D4F' },
  { id: 'LOST',      label: 'Lost',      dot: '#9B2335' },
];

// Seed leads used as fallback when API returns empty
const SEED_LEADS = [
  { id: 'L-1',  first: 'Rae',     last: 'Tomlinson', email: 'rae.t@example.com',        phone: '+1 (403) 555-0182', status: 'NEW',       source: 'Google',    owner: 'KS', notes: 'Asking about Invisalign — has Manulife insurance, husband already a patient.' },
  { id: 'L-2',  first: 'Dimitri', last: 'Voss',      email: 'dimitri.voss@example.com', phone: '+1 (587) 555-0099', status: 'NEW',       source: 'Referral',  owner: 'KS', notes: 'Referred by P-018342 (Stevens). Interested in cosmetic consult.' },
  { id: 'L-3',  first: 'Aanya',   last: 'Patel',     email: 'aanya.p@example.com',      phone: '+1 (780) 555-0224', status: 'NEW',       source: 'Instagram', owner: 'HL', notes: '' },
  { id: 'L-4',  first: 'Tom',     last: 'Brennan',   email: 'tbrennan@example.com',     phone: '+1 (403) 555-0319', status: 'CONTACTED', source: 'Google',    owner: 'KS', notes: 'Voicemail Apr 28 · followed up by email Apr 30. Awaiting reply.' },
  { id: 'L-5',  first: 'Linh',    last: 'Nguyen',    email: 'linh.n@example.com',       phone: '+1 (403) 555-0431', status: 'CONTACTED', source: 'Walk-in',   owner: 'HL', notes: 'Came by front desk · had x-rays from previous clinic.' },
  { id: 'L-6',  first: 'Joaquin', last: 'Ramos',     email: 'jramos@example.com',       phone: '+1 (587) 555-0540', status: 'QUALIFIED', source: 'Referral',  owner: 'SL', notes: 'Confirmed insurance · ready to book. Wants Saturday.' },
  { id: 'L-7',  first: 'Hana',    last: 'Park',      email: 'hana.p@example.com',       phone: '+1 (780) 555-0612', status: 'QUALIFIED', source: 'Google',    owner: 'KS', notes: 'Pre-auth submitted to Sun Life · waiting on response.' },
  { id: 'L-8',  first: 'Marcus',  last: 'Reilly',    email: 'mreilly@example.com',      phone: '+1 (403) 555-0728', status: 'CONVERTED', source: 'Google',    owner: 'HL', notes: 'Booked May 2 · first appointment scheduled.' },
  { id: 'L-9',  first: 'Ines',    last: 'Sokolova',  email: 'ines.s@example.com',       phone: '+1 (587) 555-0844', status: 'CONVERTED', source: 'Instagram', owner: 'KS', notes: 'Now patient P-018612.' },
  { id: 'L-10', first: 'Pat',     last: 'Sanderson', email: 'pat.s@example.com',        phone: '+1 (403) 555-0961', status: 'LOST',      source: 'Google',    owner: 'KS', notes: 'Found a closer clinic — politely closed.' },
];

type Lead = {
  id: string; first: string; last: string; email: string; phone: string;
  status: string; source: string; owner: string; notes: string;
};

const SmsIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;
const EmailIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>;
const CallIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>;
const NoteIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>;
const MeetingIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;

const ACTIVITY_ICON: Record<string, React.ReactNode> = {
  sms: <SmsIcon />, email: <EmailIcon />, call: <CallIcon />, note: <NoteIcon />, meeting: <MeetingIcon />,
};

function addToast(setToasts: React.Dispatch<React.SetStateAction<{id: number; msg: string}[]>>, msg: string) {
  const id = Date.now();
  setToasts(t => [...t, { id, msg }]);
  setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3000);
}

export default function CrmPage() {
  const [selected, setSelected] = useState('L-1');
  const [tab, setTab] = useState<'detail' | 'activity' | 'convert'>('activity');
  const [toasts, setToasts] = useState<{id: number; msg: string}[]>([]);
  const toast = (msg: string) => addToast(setToasts, msg);

  const { data: apiLeads } = useQuery<Lead[]>({
    queryKey: ['leads'],
    queryFn: () => fetcher<Lead[]>('/api/leads'),
  });

  const leads: Lead[] = (apiLeads && apiLeads.length > 0) ? apiLeads : SEED_LEADS;
  const lead = leads.find(l => l.id === selected) || leads[0];

  const active = leads.filter(l => l.status !== 'CONVERTED' && l.status !== 'LOST').length;
  const converted = leads.filter(l => l.status === 'CONVERTED').length;
  const conversion = leads.length ? Math.round((converted / leads.length) * 100) : 0;

  return (
    <>
      <div className={styles.stage}>
        <div className={styles.body}>
          <div className={styles.pageHeader}>
            <div>
              <h1 className={styles.pageTitle}>CRM · Leads</h1>
              <div className={styles.pageSub}>{active} active leads · {converted} converted this month · {conversion}% conversion · 3 owners</div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-ghost btn-md" onClick={() => toast('CSV import wizard would open here.')}>Import CSV</button>
              <button className="btn btn-ghost btn-md" onClick={() => toast('Campaign manager would open here.')}>Campaigns</button>
              <button className="btn btn-primary btn-md" onClick={() => toast('New lead form would open here.')}>+ New lead</button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
            <KpiTile label="Active leads"      value={String(active)}    delta="+ 6"    trend="up" accent="steel" />
            <KpiTile label="Converted · 30d"   value={String(converted)} delta="+ 2"    trend="up" accent="steel" />
            <KpiTile label="Conversion rate"   value={`${conversion}%`}  delta="+ 4.2%" trend="up" accent="steel" />
            <KpiTile label="Avg time to first" value="4 h"               delta="– 1 h"  trend="up" accent="navy"  />
          </div>

          <div className={styles.kanban}>
            {COLUMNS.map(col => {
              const items = leads.filter(l => l.status === col.id);
              return (
                <div key={col.id} className={styles.col}>
                  <div className={styles.colHead}>
                    <span className={styles.colLabel}>
                      <span className={styles.colDot} style={{ background: col.dot }} />
                      {col.label}
                    </span>
                    <span className={styles.colCount}>{items.length}</span>
                  </div>
                  {items.length === 0 && (
                    <div style={{ textAlign: 'center', color: '#8A9BB0', fontSize: '.74rem', padding: '24px 0', fontFamily: 'Inter, sans-serif' }}>Drop leads here</div>
                  )}
                  {items.map(l => (
                    <div
                      key={l.id}
                      className={`${styles.leadCard}${selected === l.id ? ' ' + styles.selected : ''}`}
                      onClick={() => setSelected(l.id)}
                    >
                      <div className={styles.leadName}>
                        <span>{l.first} {l.last}</span>
                        <span className={styles.leadSource}>{l.source}</span>
                      </div>
                      <div className={styles.leadContact}>
                        <CallIcon />
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.72rem' }}>{l.phone}</span>
                      </div>
                      {l.notes && <div className={styles.leadNotes}>{l.notes}</div>}
                      <div className={styles.leadFoot}>
                        <span className={styles.leadOwner}>
                          <span className={styles.avatarMini}>{l.owner}</span>
                          {l.id}
                        </span>
                        <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '.68rem', color: '#3A7FBD', cursor: 'pointer', fontWeight: 600 }}>Actions ▾</span>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>

          <div className={styles.drawerGrid}>
            <div className={styles.panel}>
              <div className={styles.panelHeader}>
                <div>
                  <div className={styles.panelHTitle}>{lead.first} {lead.last}</div>
                  <div className={styles.panelHSub}>
                    {lead.id} · <StatusPill kind="lead" value={lead.status} /> · Owner {lead.owner} · Source {lead.source}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-ghost btn-sm" onClick={() => toast('Lead archived.')}>Archive</button>
                  <button className="btn btn-primary btn-sm" onClick={() => toast('Conversion workflow would start here.')}>Convert to patient</button>
                </div>
              </div>

              <div className={styles.drawerTabs}>
                {(['detail', 'activity', 'convert'] as const).map(t => (
                  <span key={t} className={`${styles.drawerTab}${tab === t ? ' ' + styles.active : ''}`} onClick={() => setTab(t)}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </span>
                ))}
              </div>

              {tab === 'detail' && (
                <div className={styles.fieldGrid}>
                  <div className={styles.field}><label>First name</label><input defaultValue={lead.first} /></div>
                  <div className={styles.field}><label>Last name</label><input defaultValue={lead.last} /></div>
                  <div className={styles.field}><label>Phone</label><input defaultValue={lead.phone} style={{ fontFamily: "'JetBrains Mono', monospace" }} /></div>
                  <div className={styles.field}><label>Email</label><input defaultValue={lead.email} type="email" /></div>
                  <div className={styles.field}><label>Owner</label>
                    <select defaultValue={lead.owner}>
                      <option value="HL">Dr Hau Le</option>
                      <option value="SL">Dr Sara Lim</option>
                      <option value="KS">Kim Sato (front desk)</option>
                    </select>
                  </div>
                  <div className={styles.field}><label>Status</label>
                    <select defaultValue={lead.status}>
                      {COLUMNS.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                    </select>
                  </div>
                  <div className={`${styles.field} ${styles.full}`}><label>Notes</label><textarea defaultValue={lead.notes} /></div>
                  <div className={styles.full} style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => setTab('detail')}>Cancel</button>
                    <button className="btn btn-primary btn-sm" onClick={() => toast('Lead details saved.')}>Save</button>
                  </div>
                </div>
              )}

              {tab === 'activity' && (
                <div>
                  <div className={styles.panelPadSm} style={{ background: 'var(--rr-warm-white)', border: '1px solid var(--rr-parchment)', borderRadius: 6, marginBottom: 14 }}>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                      {['Note', 'Call', 'Email', 'SMS', 'Meeting'].map((t, i) => (
                        <span key={t} style={{
                          height: 28, padding: '0 12px', borderRadius: 999, border: '1px solid var(--rr-parchment)',
                          background: i === 0 ? 'var(--rr-mist)' : '#fff', color: i === 0 ? 'var(--rr-navy-800)' : 'var(--rr-slate-dark)',
                          fontFamily: 'Inter, sans-serif', fontSize: '.72rem', fontWeight: i === 0 ? 600 : 400, cursor: 'pointer', display: 'inline-flex', alignItems: 'center',
                        }}>{t}</span>
                      ))}
                    </div>
                    <textarea placeholder="Add a note · what was discussed, next steps, follow-up date…" rows={2} style={{ width: '100%', padding: 10, border: '1px solid var(--rr-parchment)', borderRadius: 4, fontFamily: 'Inter, sans-serif', fontSize: '.84rem', color: 'var(--rr-ink)', resize: 'vertical', boxSizing: 'border-box' }} />
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
                      <button className="btn btn-primary btn-sm" onClick={() => toast('Activity logged.')}>Log activity</button>
                    </div>
                  </div>
                  <div>
                    {SEED_ACTIVITIES.map(a => (
                      <div key={a.id} className={styles.timelineRow}>
                        <span className={`${styles.timelineIcon} ${styles[`ti_${a.icon}` as keyof typeof styles]}`}>{ACTIVITY_ICON[a.icon]}</span>
                        <div className={styles.tiBody}>
                          <div className={styles.tiHead}>
                            <span className={styles.tiKind}>{a.kind.charAt(0).toUpperCase() + a.kind.slice(1)}</span>
                            <span className={styles.tiWhen}>{a.when}</span>
                          </div>
                          <div className={styles.tiText}>{a.body}</div>
                          <div className={styles.tiAuthor}>— {a.author}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {tab === 'convert' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '8px 0' }}>
                  <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '.88rem', color: 'var(--rr-ink)', margin: 0, lineHeight: 1.6 }}>
                    Convert <strong>{lead.first} {lead.last}</strong> into a patient record. The lead history, notes, and activity timeline carry over to the new chart.
                  </p>
                  <div className={styles.field}><label>Insurance carrier</label>
                    <select><option>Self pay</option><option>Manulife</option><option>Sun Life</option><option>Alberta Blue Cross</option></select>
                  </div>
                  <div className={styles.field}><label>First appointment</label><input type="text" defaultValue="2026-05-04 · 10:30 · Op 3 · Hyg. Renu" /></div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => setTab('detail')}>Cancel</button>
                    <button className="btn btn-primary btn-sm" onClick={() => toast('Patient record created from lead ' + lead.id + '.')}>Convert to patient</button>
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className={styles.panel}>
                <div className={styles.panelHeader}>
                  <div>
                    <div className={styles.panelHTitle}>Source breakdown</div>
                    <div className={styles.panelHSub}>30 days · leads · conversion rate</div>
                  </div>
                </div>
                {SEED_SOURCES.map(s => (
                  <div key={s.name} className={styles.srcRow}>
                    <span style={{ minWidth: 86 }}>{s.name}</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.78rem', color: '#1C2333', minWidth: 30, textAlign: 'right' }}>{s.leads}</span>
                    <span className={styles.srcBar}><span className={styles.srcBarFill} style={{ width: `${s.conv_rate * 2}%` }} /></span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.78rem', color: '#3A7FBD', fontWeight: 600, minWidth: 40, textAlign: 'right' }}>{s.conv_rate}%</span>
                  </div>
                ))}
              </div>

              <div className={styles.panel}>
                <div className={styles.panelHeader}>
                  <div>
                    <div className={styles.panelHTitle}>Tasks &amp; follow-ups</div>
                    <div className={styles.panelHSub}>Owned by you · 4 due today</div>
                  </div>
                </div>
                <div>
                  {SEED_TASKS.map((t, i) => (
                    <div key={i} className={styles.srcRow} style={{ padding: '11px 0' }}>
                      <span className={`${styles.timelineIcon} ${styles[`ti_${t.kind}` as keyof typeof styles]}`} style={{ width: 22, height: 22, marginRight: 10 }}>{ACTIVITY_ICON[t.kind]}</span>
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <span style={{ fontFamily: 'Inter, sans-serif', fontWeight: 600, fontSize: '.84rem', color: '#1C2333' }}>{t.what}</span>
                        <span style={{ fontFamily: 'Inter, sans-serif', fontSize: '.72rem', color: '#8A9BB0' }}>{t.who}</span>
                      </div>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.7rem', color: '#B45309', fontWeight: 600 }}>{t.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: 'Inter, sans-serif', fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>
            ROCKYRIDGE · DENTAL AI · v1
          </div>
        </div>
      </div>

      {toasts.length > 0 && (
        <div className={styles.toastCtr}>
          {toasts.map(t => <div key={t.id} className={styles.toastMsg}>{t.msg}</div>)}
        </div>
      )}
    </>
  );
}
