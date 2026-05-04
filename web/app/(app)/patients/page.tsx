'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '@/lib/api/client';
import { KpiTile } from '@/components/dental/KpiTile';
import { StatusPill } from '@/components/dental/StatusPill';
import { EmptyState } from '@/components/dental/EmptyState';
import { ToothChartTile } from '@/components/dental/ToothChartTile';
import styles from './page.module.css';

interface Patient {
  id: string;
  first: string;
  last: string;
  dob?: string;
  insurance?: string;
  last_visit?: string;
  status?: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
}

interface PatientsResponse {
  items?: Patient[];
  total?: number;
}

const STATUS_TONE: Record<string, { bg: string; fg: string; avatar: string }> = {
  active:   { bg: '#E8F5EE', fg: '#2A7D4F', avatar: '#3A7FBD' },
  recall:   { bg: '#FDF3E5', fg: '#B45309', avatar: '#B45309' },
  plan:     { bg: '#D9EAF5', fg: '#2E6494', avatar: '#6BAED6' },
  inactive: { bg: '#F5F2EC', fg: '#4A5568', avatar: '#8A9BB0' },
};

const FILTERS = ['All', 'Active', 'Recall due', 'Plan in progress', 'Inactive'];

const DETAIL_TABS = ['Overview', 'Appointments', 'Insurance', 'Notes'];

function normalizePatient(p: Patient): Patient {
  return {
    ...p,
    first: p.first ?? p.first_name ?? '',
    last: p.last ?? p.last_name ?? '',
    dob: p.dob ?? p.date_of_birth ?? '',
    status: p.status ?? 'active',
  };
}

function CenterModal({ onClose, children }: { onClose: () => void; children: React.ReactNode }) {
  return (
    <div className={styles.centerModalBackdrop} onClick={onClose}>
      <div className={styles.centerModal} onClick={e => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

function PatientDetail({ patient, onClose }: { patient: Patient; onClose: () => void }) {
  const [tab, setTab] = useState('Overview');
  const p = normalizePatient(patient);
  const initials = ((p.first[0] ?? '') + (p.last[0] ?? '')).toUpperCase();
  const tone = STATUS_TONE[p.status ?? 'active'] ?? STATUS_TONE.active;

  return (
    <CenterModal onClose={onClose}>
      <div className={styles.centerModalTopbar}>
        <button className={styles.drawerBack} onClick={onClose}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
        </button>
        <span className={styles.backLabel}>Back to The Roster</span>
      </div>
      <div className={styles.centerModalBody}>
        <div className={styles.apptWsHero}>
          <div className={styles.apptWsAva} style={{ background: tone.avatar }}>{initials}</div>
          <div className={styles.apptWsInfo}>
            <div className={styles.apptWsName}>{p.first} {p.last}</div>
            <div className={styles.apptWsDetail}>Provider · Dr Hau Le</div>
            <div className={styles.apptWsId}>{p.id} · {p.dob} · {p.insurance}</div>
          </div>
          <span style={{ fontSize: '.68rem', fontWeight: 600, padding: '4px 12px', borderRadius: 999, letterSpacing: '.06em', textTransform: 'uppercase', background: tone.bg, color: tone.fg }}>{p.status}</span>
        </div>

        <div className={styles.tabBar}>
          {DETAIL_TABS.map(t => (
            <button key={t} className={`${styles.tabBtn}${tab === t ? ' ' + styles.tabBtnActive : ''}`} onClick={() => setTab(t)}>{t}</button>
          ))}
        </div>

        {tab === 'Overview' && (
          <>
            <div>
              <div className={styles.detailRow}><span className={styles.detailK}>Date of birth</span><span className={styles.detailV}>{p.dob}</span></div>
              <div className={styles.detailRow}><span className={styles.detailK}>Insurance</span><span className={styles.detailV}>{p.insurance}</span></div>
              <div className={styles.detailRow}><span className={styles.detailK}>Last visit</span><span className={styles.detailV}>{p.last_visit}</span></div>
              <div className={styles.detailRow}><span className={styles.detailK}>Status</span><span className={styles.detailV}>{p.status}</span></div>
            </div>
            <ToothChartTile />
          </>
        )}

        {tab === 'Insurance' && (
          <div>
            <div className={styles.detailRow}><span className={styles.detailK}>Provider</span><span className={styles.detailV}>{p.insurance}</span></div>
            <div className={styles.detailRow}><span className={styles.detailK}>Policy</span><span className={styles.detailV} style={{ fontFamily: 'var(--font-mono)' }}>GRP-{p.id.slice(2)}-01</span></div>
            <div className={styles.detailRow}><span className={styles.detailK}>Coverage</span><span className={styles.detailV}>80% preventive · 50% major</span></div>
            <div className={styles.detailRow}><span className={styles.detailK}>Annual max</span><span className={styles.detailV} style={{ fontFamily: 'var(--font-mono)' }}>$2,500.00</span></div>
          </div>
        )}

        {tab === 'Notes' && (
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.88rem', color: 'var(--rr-slate-dark)', padding: '12px 0' }}>
            <div style={{ marginBottom: 12, padding: '14px 16px', border: '1px solid var(--rr-parchment)', borderRadius: 6 }}>
              <div style={{ fontWeight: 600, color: 'var(--rr-ink)', marginBottom: 4 }}>Clinical note — 2026-04-21</div>
              <div>Patient reports no discomfort. Recall completed. Next visit in 6 months.</div>
            </div>
            <div style={{ padding: '14px 16px', border: '1px solid var(--rr-parchment)', borderRadius: 6 }}>
              <div style={{ fontWeight: 600, color: 'var(--rr-ink)', marginBottom: 4 }}>Admin note — 2026-03-10</div>
              <div>Insurance verification completed. Pre-auth submitted for crown #36.</div>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <button className="btn btn-primary btn-md" onClick={onClose}>Open full chart</button>
          <button className="btn btn-ghost btn-md" onClick={onClose}>Close</button>
        </div>
      </div>
    </CenterModal>
  );
}

function NewPatientDrawer({ onClose, onSave }: { onClose: () => void; onSave: (p: Patient) => void }) {
  const [first, setFirst] = useState('');
  const [last, setLast] = useState('');
  const [dob, setDob] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [insurance, setInsurance] = useState('');
  const [isMinor, setIsMinor] = useState(false);
  const [guardian, setGuardian] = useState('');
  const [consent, setConsent] = useState(false);

  const handleSave = () => {
    const id = 'P-' + String(Math.floor(10000 + Math.random() * 90000));
    onSave({ id, first, last, dob, insurance, last_visit: 'New', status: 'active' });
  };

  return (
    <>
      <div className={styles.drawerOverlay} onClick={onClose} />
      <aside className={styles.drawer} role="dialog">
        <div className={styles.drawerHeader}>
          <div style={{ display: 'flex', alignItems: 'flex-start' }}>
            <button className={styles.drawerBack} onClick={onClose}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
            </button>
            <div>
              <div className={styles.drawerMeta}>New patient</div>
              <div className={styles.drawerTitle}>Add a new patient</div>
              <div className={styles.drawerSub}>Fill in patient details below.</div>
            </div>
          </div>
          <button className={styles.drawerX} onClick={onClose}>&times;</button>
        </div>
        <div className={styles.drawerBody}>
          <div className={styles.fieldRow}>
            <div className={styles.field}><label className={styles.lbl}>First name *</label><input className={styles.dInput} value={first} onChange={e => setFirst(e.target.value)} /></div>
            <div className={styles.field}><label className={styles.lbl}>Last name *</label><input className={styles.dInput} value={last} onChange={e => setLast(e.target.value)} /></div>
          </div>
          <div className={styles.field}><label className={styles.lbl}>Date of birth</label><input type="date" className={styles.dInput} value={dob} onChange={e => setDob(e.target.value)} /></div>
          <div className={styles.fieldRow}>
            <div className={styles.field}><label className={styles.lbl}>Phone</label><input className={styles.dInput} value={phone} onChange={e => setPhone(e.target.value)} /></div>
            <div className={styles.field}><label className={styles.lbl}>Email</label><input className={styles.dInput} value={email} onChange={e => setEmail(e.target.value)} /></div>
          </div>
          <div className={styles.field}><label className={styles.lbl}>Insurance provider</label><input className={styles.dInput} value={insurance} onChange={e => setInsurance(e.target.value)} /></div>
          <div className={styles.field} style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" id="isMinor" checked={isMinor} onChange={e => setIsMinor(e.target.checked)} />
            <label htmlFor="isMinor" className={styles.lbl} style={{ marginBottom: 0 }}>Patient is a minor</label>
          </div>
          {isMinor && <div className={styles.field}><label className={styles.lbl}>Guardian name</label><input className={styles.dInput} value={guardian} onChange={e => setGuardian(e.target.value)} /></div>}
          <div className={styles.field} style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" id="consent" checked={consent} onChange={e => setConsent(e.target.checked)} />
            <label htmlFor="consent" className={styles.lbl} style={{ marginBottom: 0 }}>Consent approved</label>
          </div>
        </div>
        <div className={styles.drawerFooter}>
          <button className="btn btn-ghost btn-md" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary btn-md" disabled={!first || !last} onClick={handleSave}>Save patient</button>
        </div>
      </aside>
    </>
  );
}

export default function PatientsPage() {
  const router = useRouter();
  const [filter, setFilter] = useState('All');
  const [query, setQuery] = useState('');
  const [activePatient, setActivePatient] = useState<Patient | null>(null);
  const [newPatientOpen, setNewPatientOpen] = useState(false);
  const [toasts, setToasts] = useState<{ id: number; msg: string; detail?: string }[]>([]);
  const [localPatients, setLocalPatients] = useState<Patient[]>([]);

  const addToast = (msg: string, detail?: string) => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, detail }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  };

  const { data } = useQuery<PatientsResponse | Patient[]>({
    queryKey: ['patients', 'list'],
    queryFn: () => fetcher<PatientsResponse | Patient[]>('/api/patients?page=1&limit=500'),
  });

  const apiPatients: Patient[] = Array.isArray(data) ? data : (data?.items ?? []);
  const allPatients = [...apiPatients, ...localPatients].map(normalizePatient);

  const rows = allPatients.filter(p => {
    if (filter === 'Active' && p.status !== 'active') return false;
    if (filter === 'Recall due' && p.status !== 'recall') return false;
    if (filter === 'Plan in progress' && p.status !== 'plan') return false;
    if (filter === 'Inactive' && p.status !== 'inactive') return false;
    if (query) {
      const q = query.toLowerCase();
      return `${p.first} ${p.last} ${p.id} ${p.insurance ?? ''}`.toLowerCase().includes(q);
    }
    return true;
  });

  const recallRows = allPatients.filter(p => p.status === 'recall' || p.status === 'inactive').slice(0, 4);

  return (
    <>
      <div className={styles.body}>
        {/* Page header */}
        <div className={styles.pageHeader}>
          <div>
            <h1 className={styles.pageTitle}>Patients</h1>
            <div className={styles.pageSub}>{allPatients.length} on file · 2 due for recall this week · last sync 2 min ago</div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-ghost btn-md" onClick={() => addToast('CSV import started.', 'Processing file...')}>Import CSV</button>
            <button className="btn btn-primary btn-md" onClick={() => setNewPatientOpen(true)}>+ New patient</button>
          </div>
        </div>

        {/* KPI strip */}
        <div className={styles.kpiRow}>
          <KpiTile label="Total active"   value="1,284" delta="+ 18" trend="up"   accent="steel" />
          <KpiTile label="New this month" value="42"    delta="+ 6"  trend="up"   accent="steel" />
          <KpiTile label="Recall due"     value="38"    delta="– 4"  trend="up"   accent="navy"  />
          <KpiTile label="Plans pending"  value="11"    delta="+ 2"  trend="down" accent="steel" />
        </div>

        {/* Patient list panel */}
        <div className={styles.panel}>
          <div className={styles.toolbar} style={{ marginBottom: 18 }}>
            <input
              type="text"
              placeholder="Search by name, ID, or insurance…"
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
            {FILTERS.map(f => (
              <button
                key={f}
                className={`${styles.filterPill}${filter === f ? ' ' + styles.filterPillActive : ''}`}
                onClick={() => setFilter(f)}
              >{f}</button>
            ))}
            <button className={styles.filterPill} style={{ marginLeft: 'auto' }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              Sort: Last visit
            </button>
          </div>

          {rows.length === 0 ? (
            <EmptyState
              title="No patients match"
              body={`Nothing in the chart matches "${query || filter}". Try clearing filters or searching by chart ID.`}
              ctaLabel="Clear filters"
              onCta={() => { setFilter('All'); setQuery(''); }}
            />
          ) : (
            <table className={styles.list}>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Chart ID</th>
                  <th>Date of birth</th>
                  <th>Insurance</th>
                  <th>Last visit</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map(p => {
                  const tone = STATUS_TONE[p.status ?? 'active'] ?? STATUS_TONE.active;
                  const initials = ((p.first[0] ?? '') + (p.last[0] ?? '')).toUpperCase();
                  return (
                    <tr key={p.id} onClick={() => router.push(`/patients/${p.id}`)} style={{ cursor: 'pointer' }}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <span className={styles.avatarSm} style={{ background: tone.avatar }}>{initials}</span>
                          <div>
                            <div style={{ fontWeight: 600, color: '#1C2333' }}>{p.first} {p.last}</div>
                            <div style={{ fontSize: '.72rem', color: '#8A9BB0' }}>Provider · Dr Hau Le</div>
                          </div>
                        </div>
                      </td>
                      <td className={styles.idCell}>{p.id}</td>
                      <td className={styles.idCell}>{p.dob}</td>
                      <td>{p.insurance}</td>
                      <td className={styles.idCell}>{p.last_visit}</td>
                      <td><StatusPill kind="patient_lifecycle" value={p.status ?? 'active'} /></td>
                      <td style={{ textAlign: 'right' }}>
                        <a className={styles.panelHAction} href={`/patients/${p.id}`} onClick={e => { e.stopPropagation(); }}>Open chart →</a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Recall queue panel */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <div className={styles.panelHTitle}>Recall queue</div>
              <div className={styles.panelHSub}>Patients overdue for hygiene · top 4</div>
            </div>
            <a className={styles.panelHAction} href="/patients?filter=recall">Open recall workflow →</a>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {recallRows.map(p => (
              <a key={p.id} href={`/patients/${p.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'flex', border: '1px solid #EDE9E0', borderRadius: 6, padding: '14px 16px', flexDirection: 'column', gap: 6, cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={styles.avatarSm} style={{ background: STATUS_TONE[p.status ?? 'active']?.avatar ?? '#8A9BB0' }}>{((p.first[0] ?? '') + (p.last[0] ?? '')).toUpperCase()}</span>
                  <div style={{ fontWeight: 600, color: '#1C2333', fontSize: '.88rem' }}>{p.first} {p.last}</div>
                </div>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.7rem', color: '#8A9BB0' }}>{p.id} · last seen {p.last_visit}</div>
                <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                  <button className="btn btn-ghost btn-sm" onClick={e => { e.preventDefault(); e.stopPropagation(); addToast('SMS sent.', `${p.first} ${p.last}`); }}>SMS</button>
                  <button className="btn btn-primary btn-sm" onClick={e => { e.preventDefault(); e.stopPropagation(); addToast('Recall booked.', `${p.first} ${p.last}`); }}>Book recall</button>
                </div>
              </a>
            ))}
          </div>
        </div>

        <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>
          ROCKYRIDGE · DENTAL AI · v1
        </div>
      </div>

      {activePatient && <PatientDetail patient={activePatient} onClose={() => setActivePatient(null)} />}
      {newPatientOpen && (
        <NewPatientDrawer
          onClose={() => setNewPatientOpen(false)}
          onSave={p => {
            setLocalPatients(prev => [...prev, p]);
            setNewPatientOpen(false);
            addToast('Patient created.', `${p.first} ${p.last} · ${p.id}`);
          }}
        />
      )}

      {toasts.length > 0 && (
        <div className={styles.toastStack}>
          {toasts.map(t => (
            <div key={t.id} className={`${styles.toast} ${styles.toastSuccess}`}>
              <svg className={styles.toastIco} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              <div className={styles.toastBody}>{t.msg}{t.detail && <span className={styles.toastDetail}>{t.detail}</span>}</div>
              <button className={styles.toastX} onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))}>&times;</button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
