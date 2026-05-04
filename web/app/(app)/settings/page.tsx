'use client';
import React, { useState } from 'react';
import { LockedFeature } from '@/components/dental/LockedFeature';
import styles from './page.module.css';

const TABS = ['Clinic info','Working hours','Operatories','Providers','Users & roles','Integrations','Notifications','Audit log','AI Greeting','AI Routing','AI Services','AI Knowledge'];
const DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

const OPERATORIES = [
  { name: 'Op 1', tags: ['chair','x-ray'], active: true },
  { name: 'Op 2', tags: ['chair','panoramic'], active: true },
  { name: 'Op 3', tags: ['chair'], active: false },
];

const PROVIDERS_DATA = [
  { name: 'Dr. Hau Le',    title: 'Denturist',  specialty: 'Complete dentures', active: true },
  { name: 'Dr. Sara Osei', title: 'Dentist',    specialty: 'General dentistry', active: true },
  { name: 'Dr. Raj Patel', title: 'Hygienist',  specialty: 'Periodontics',      active: true },
];

const USERS_DATA = [
  { full_name: 'Hau Le',    email: 'hau@oakdental.ca',  role: 'admin' },
  { full_name: 'Sara Osei', email: 'sara@oakdental.ca', role: 'provider' },
  { full_name: 'Mia Tran',  email: 'mia@oakdental.ca',  role: 'receptionist' },
];

const AUDIT_DATA = [
  { action: 'UPDATE', entity: 'Patient #P-1042',        user: 'Hau Le',    when: '2026-05-02 14:32' },
  { action: 'CREATE', entity: 'Invoice INV-2026-0418',  user: 'Mia Tran',  when: '2026-05-02 11:10' },
  { action: 'DELETE', entity: 'Appointment #A-0091',    user: 'Sara Osei', when: '2026-05-01 09:44' },
];

// TODO: wire to dental-agent — endpoint not yet implemented
const SERVICES_SEED = [
  { id: 'SVC-001', name: 'Recall Exam',              duration_min: 30,  base_price: 80.00   },
  { id: 'SVC-002', name: 'Scaling — Full Mouth',     duration_min: 60,  base_price: 220.00  },
  { id: 'SVC-003', name: 'Composite Restoration',    duration_min: 45,  base_price: 180.00  },
  { id: 'SVC-004', name: 'Crown Preparation',        duration_min: 90,  base_price: 1180.00 },
  { id: 'SVC-005', name: 'Crown Seat',               duration_min: 45,  base_price: 1220.00 },
  { id: 'SVC-006', name: 'Complete Denture — Upper', duration_min: 60,  base_price: 1650.00 },
  { id: 'SVC-007', name: 'Implant Placement',        duration_min: 90,  base_price: 2400.00 },
  { id: 'SVC-008', name: 'New Patient Consult',      duration_min: 60,  base_price: 120.00  },
];

const AI_BOOKABLE_IDS = ['SVC-001', 'SVC-006', 'SVC-008'];

// TODO: wire to dental-agent — endpoint not yet implemented
const KNOWLEDGE_DOCS = [
  {
    filename: 'denture_faq.md',
    title: 'Denture FAQ',
    last_updated: '2026-04-12',
    word_count: 1840,
    body: '# Denture FAQ\n\nCommon questions callers ask about dentures, fittings, and aftercare.',
  },
  {
    filename: 'practice_info.md',
    title: 'Practice Info',
    last_updated: '2026-04-08',
    word_count: 920,
    body: '# Practice Info\n\nClinic location, parking, accessibility, accepted insurance.',
  },
];

const ROLE_COLORS: Record<string, string> = { admin: '#D9EAF5', provider: '#E8F5EE', receptionist: '#F5F2EC' };
const ROLE_TEXT: Record<string, string>   = { admin: '#2E6494', provider: '#2A7D4F', receptionist: '#4A5568' };

export default function SettingsPage() {
  const [tab, setTab] = useState(0);
  const [toasts, setToasts] = useState<{id: number; msg: string}[]>([]);
  const [openDoc, setOpenDoc] = useState<string | null>(null);
  const [greetingLen, setGreetingLen] = useState(0);

  const addToast = (msg: string) => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3000);
  };

  return (
    <>
      <div className={styles.body}>
        <div className={styles.pageHeader}>
          <div>
            <h1 className={styles.pageTitle}>Settings</h1>
            <p className={styles.pageSub}>Clinic configuration and system preferences</p>
          </div>
        </div>

        <div className={styles.panel} style={{ padding: 0 }}>
          <div className={styles.tabBar} style={{ padding: '0 24px' }}>
            {TABS.map((t, i) => (
              <button key={t} className={`${styles.tabBtn}${tab === i ? ' ' + styles.tabBtnActive : ''}`} onClick={() => setTab(i)}>{t}</button>
            ))}
          </div>

          <div style={{ padding: '24px' }}>
            {tab === 0 && (
              <div style={{ maxWidth: 560 }}>
                <div className={styles.fieldRow}>
                  <div className={styles.field}><label className={styles.lbl}>Clinic name</label><input className={styles.dInput} defaultValue="Oak Dental Calgary" /></div>
                  <div className={styles.field}><label className={styles.lbl}>Display name</label><input className={styles.dInput} defaultValue="Oak Dental" /></div>
                </div>
                <div className={styles.field}><label className={styles.lbl}>Timezone</label><input className={styles.dInput} defaultValue="America/Edmonton" /></div>
                <div className={styles.field}><label className={styles.lbl}>Address</label><input className={styles.dInput} defaultValue="1234 Macleod Trail SE, Calgary, AB T2G 0A1" /></div>
                <div className={styles.fieldRow}>
                  <div className={styles.field}><label className={styles.lbl}>Contact phone</label><input className={styles.dInput} defaultValue="+1 403 555 0100" /></div>
                  <div className={styles.field}><label className={styles.lbl}>Booking notification email</label><input className={styles.dInput} defaultValue="bookings@oakdental.ca" /></div>
                </div>
                <button className="btn btn-primary btn-sm" style={{ marginTop: 8 }} onClick={() => addToast('Clinic info saved.')}>Save changes</button>
              </div>
            )}

            {tab === 1 && (
              <table className={styles.list}>
                <thead><tr><th>Day</th><th>Open</th><th>Close</th><th>Lunch start</th><th>Lunch end</th><th>Closed</th></tr></thead>
                <tbody>
                  {DAYS.map((d, i) => (
                    <tr key={d}>
                      <td>{d}</td>
                      <td><input className={styles.dInput} style={{ width: 80 }} defaultValue={i === 0 || i === 6 ? '—' : '08:00'} /></td>
                      <td><input className={styles.dInput} style={{ width: 80 }} defaultValue={i === 0 || i === 6 ? '—' : '17:00'} /></td>
                      <td><input className={styles.dInput} style={{ width: 80 }} defaultValue={i === 0 || i === 6 ? '—' : '12:00'} /></td>
                      <td><input className={styles.dInput} style={{ width: 80 }} defaultValue={i === 0 || i === 6 ? '—' : '13:00'} /></td>
                      <td><input type="checkbox" defaultChecked={i === 0 || i === 6} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {tab === 2 && (
              <table className={styles.list}>
                <thead><tr><th>Name</th><th>Equipment tags</th><th>Active</th></tr></thead>
                <tbody>
                  {OPERATORIES.map(o => (
                    <tr key={o.name}>
                      <td>{o.name}</td>
                      <td>{o.tags.map(t => <span key={t} className={styles.pill} style={{ background: 'var(--rr-mist)', color: 'var(--rr-steel-700)', marginRight: 4 }}>{t}</span>)}</td>
                      <td><span className={`${styles.pill} ${o.active ? styles.pillActive : styles.pillInactive}`}>{o.active ? 'Active' : 'Inactive'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {tab === 3 && (
              <table className={styles.list}>
                <thead><tr><th>Name</th><th>Title</th><th>Specialty</th><th>Status</th></tr></thead>
                <tbody>
                  {PROVIDERS_DATA.map(p => (
                    <tr key={p.name}>
                      <td>{p.name}</td>
                      <td>{p.title}</td>
                      <td>{p.specialty}</td>
                      <td><span className={`${styles.pill} ${p.active ? styles.pillActive : styles.pillInactive}`}>{p.active ? 'Active' : 'Inactive'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {tab === 4 && (
              <table className={styles.list}>
                <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
                <tbody>
                  {USERS_DATA.map(u => (
                    <tr key={u.email}>
                      <td>{u.full_name}</td>
                      <td className={styles.idCell}>{u.email}</td>
                      <td><span className={styles.pill} style={{ background: ROLE_COLORS[u.role] || '#F5F2EC', color: ROLE_TEXT[u.role] || '#4A5568' }}>{u.role}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {tab === 5 && (
              <LockedFeature title="Integrations" body="Integrations are paused while we rework auth and webhook signing." backHref="/settings" />
            )}

            {tab === 6 && (
              <LockedFeature title="Notifications" body="Notifications are paused while we migrate the templating engine." backHref="/settings" />
            )}

            {tab === 7 && (
              <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                <table className={styles.list}>
                  <thead><tr><th>Action</th><th>Entity</th><th>User</th><th>When</th></tr></thead>
                  <tbody>
                    {AUDIT_DATA.map((a, i) => (
                      <tr key={i}>
                        <td><span className={styles.pill} style={{ background: '#F5F2EC', color: '#4A5568' }}>{a.action}</span></td>
                        <td>{a.entity}</td>
                        <td>{a.user}</td>
                        <td className={styles.idCell}>{a.when}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {tab === 8 && (
              <div style={{ maxWidth: 720 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                  <div>
                    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Greeting</div>
                    <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)' }}>What the AI says when it picks up a call.</div>
                  </div>
                  <span className={`${styles.pill} ${styles.pillInactive}`}>Pending review</span>
                </div>
                <div className={styles.field}>
                  <label className={styles.lbl}>Greeting message</label>
                  <textarea
                    className={styles.dInput}
                    rows={4}
                    placeholder="Welcome to … How can I help you today?"
                    maxLength={400}
                    style={{ fontFamily: 'var(--font-ui)', resize: 'vertical' }}
                    onChange={(e) => setGreetingLen(e.target.value.length)}
                  />
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.74rem', color: greetingLen > 280 ? '#9B2335' : greetingLen > 240 ? '#B45309' : 'var(--rr-slate-dark)', marginTop: 4 }}>{greetingLen} / 280 characters</div>
                </div>
                <button className="btn btn-primary btn-sm" style={{ marginTop: 8 }} onClick={() => addToast('Greeting saved. Pending engineer review.')}>Save greeting</button>
                <div style={{ marginTop: 24, paddingTop: 18, borderTop: '1px solid var(--rr-parchment)' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--rr-navy-800)', marginBottom: 6 }}>Engineer approval</div>
                  <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', lineHeight: 1.5, marginBottom: 12 }}>
                    First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve.
                  </div>
                  <button className="btn btn-ghost btn-sm" disabled style={{ opacity: 0.55, cursor: 'not-allowed' }}>Approve clinic (engineer-gated)</button>
                </div>
              </div>
            )}

            {tab === 9 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.4fr) minmax(0,1fr)', gap: 24, alignItems: 'start' }}>
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Routing</div>
                  <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', marginBottom: 16 }}>How calls flow between the front desk and the AI.</div>
                  <div className={styles.fieldRow}>
                    <div className={styles.field}>
                      <label className={styles.lbl}>Timezone</label>
                      <select className={styles.dInput} defaultValue="America/Edmonton">
                        <option value="America/Edmonton">America/Edmonton</option>
                        <option value="America/Vancouver">America/Vancouver</option>
                        <option value="America/Toronto">America/Toronto</option>
                      </select>
                    </div>
                    <div className={styles.field}>
                      <label className={styles.lbl}>Ring timeout (seconds)</label>
                      <input className={styles.dInput} type="number" min={0} max={30} defaultValue={5} />
                      <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>How long the front desk rings before the AI picks up.</span>
                    </div>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.lbl}>Front desk numbers (comma-separated, E.164)</label>
                    <input className={styles.dInput} defaultValue="" placeholder="+15879738089" />
                    <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>Example: +15879738089</span>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.lbl}>Backup number (optional)</label>
                    <input className={styles.dInput} defaultValue="" />
                    <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>Used when the front desk numbers don&apos;t answer.</span>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.lbl}>AI SIP URI (read-only here; engineer-managed)</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <input className={styles.dInput} disabled value="" style={{ flex: 1, background: 'var(--rr-warm-white)', cursor: 'not-allowed' }} />
                      <span className={`${styles.pill} ${styles.pillInactive}`}>Engineer-managed</span>
                    </div>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.lbl}>Hours per weekday</label>
                    <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginBottom: 6 }}>Both blank means closed that day.</span>
                    <table className={styles.list} style={{ marginTop: 6 }}>
                      <thead><tr><th>Day</th><th>Open</th><th>Close</th></tr></thead>
                      <tbody>
                        {['mon','tue','wed','thu','fri','sat','sun'].map(d => (
                          <tr key={d}>
                            <td style={{ textTransform: 'capitalize' }}>{d}</td>
                            <td><input className={styles.dInput} style={{ width: 90 }} defaultValue="" placeholder="--:--" /></td>
                            <td><input className={styles.dInput} style={{ width: 90 }} defaultValue="" placeholder="--:--" /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.lbl}>Holidays (YYYY-MM-DD, one per line)</label>
                    <textarea className={styles.dInput} rows={3} defaultValue="" style={{ fontFamily: 'var(--font-mono)' }} />
                    <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>Add days you&apos;re closed beyond regular hours.</span>
                  </div>
                  <div className={styles.toggleRow}>
                    <div>
                      <div className={styles.toggleLabel}>AI handles after-hours calls</div>
                      <div className={styles.toggleSub}>When you&apos;re closed, the AI takes the call instead of voicemail.</div>
                    </div>
                    <input type="checkbox" defaultChecked />
                  </div>
                  <div className={styles.toggleRow}>
                    <div>
                      <div className={styles.toggleLabel}>AI handles in-hours overflow</div>
                      <div className={styles.toggleSub}>If the front desk can&apos;t pick up in time, the AI steps in.</div>
                    </div>
                    <input type="checkbox" defaultChecked />
                  </div>
                  <button className="btn btn-primary btn-sm" style={{ marginTop: 14 }} onClick={() => addToast('Routing configuration saved.')}>Save routing</button>
                </div>
                <aside style={{ position: 'sticky', top: 16, background: 'var(--rr-warm-white)', border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: 18 }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--rr-navy-800)', marginBottom: 8 }}>Preview</div>
                  <p style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', lineHeight: 1.55, marginTop: 0 }}>
                    What would the agent do at a given moment, against the currently saved rules?
                  </p>
                  <div className={styles.field}>
                    <label className={styles.lbl}>When (your local TZ)</label>
                    <input className={styles.dInput} type="datetime-local" />
                  </div>
                  <div className={styles.toggleRow} style={{ borderBottom: 'none', padding: '6px 0' }}>
                    <div className={styles.toggleLabel}>Assume AI healthy</div>
                    <input type="checkbox" defaultChecked />
                  </div>
                  <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={() => addToast('Routing preview would open here. Access requires engineer role.')}>Preview decision</button>
                </aside>
              </div>
            )}

            {tab === 10 && (
              <div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Service catalogue</div>
                <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', marginBottom: 14 }}>
                  Pick which of your services the AI is allowed to book over the phone.
                </div>
                <table className={styles.list}>
                  <thead><tr><th>Service ID</th><th>Name</th><th>Duration</th><th>Base price</th><th>AI Bookable</th></tr></thead>
                  <tbody>
                    {SERVICES_SEED.map(s => {
                      const enabled = AI_BOOKABLE_IDS.includes(s.id);
                      return (
                        <tr key={s.id}>
                          <td className={styles.idCell}>{s.id}</td>
                          <td>{s.name}</td>
                          <td className={styles.idCell}>{s.duration_min} min</td>
                          <td className={styles.idCell}>${s.base_price.toFixed(2)}</td>
                          <td>
                            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                              <input type="checkbox" defaultChecked={enabled} />
                              <span className={`${styles.pill} ${enabled ? styles.pillActive : styles.pillInactive}`}>{enabled ? 'AI Bookable' : 'Front-desk only'}</span>
                            </label>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <button className="btn btn-primary btn-sm" style={{ marginTop: 14 }} onClick={() => addToast('Service catalogue saved.')}>Save service catalogue</button>
              </div>
            )}

            {tab === 11 && (
              <div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Knowledge base</div>
                <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', marginBottom: 14 }}>
                  Edit the AI knowledge base. AI uses these files as ground truth when answering caller questions.
                </div>
                {KNOWLEDGE_DOCS.map(doc => {
                  const isOpen = openDoc === doc.filename;
                  return (
                    <div key={doc.filename} style={{ border: '1px solid var(--rr-parchment)', borderRadius: 6, marginBottom: 10, overflow: 'hidden' }}>
                      <div onClick={() => setOpenDoc(isOpen ? null : doc.filename)}
                           style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', cursor: 'pointer', background: isOpen ? 'var(--rr-warm-white)' : '#fff' }}>
                        <div>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--rr-slate-dark)' }}>{doc.filename}</div>
                          <div style={{ fontFamily: 'var(--font-ui)', fontWeight: 600, fontSize: '0.92rem', color: 'var(--rr-navy-800)', marginTop: 2 }}>{doc.title}</div>
                        </div>
                        <div style={{ display: 'flex', gap: 18, alignItems: 'center', fontFamily: 'var(--font-ui)', fontSize: '0.78rem', color: 'var(--rr-slate-dark)' }}>
                          <span>Last updated: {doc.last_updated}</span>
                          <span>Word count: {doc.word_count}</span>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 200ms' }}><polyline points="6 9 12 15 18 9"/></svg>
                        </div>
                      </div>
                      {isOpen && (
                        <div style={{ padding: '14px 18px', borderTop: '1px solid var(--rr-parchment)', background: '#fff' }}>
                          <textarea className={styles.dInput} rows={10} defaultValue={doc.body} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', resize: 'vertical' }} />
                        </div>
                      )}
                    </div>
                  );
                })}
                <button className="btn btn-primary btn-sm" style={{ marginTop: 14 }} onClick={() => addToast('Knowledge base updated.')}>Save knowledge updates</button>
              </div>
            )}
          </div>
        </div>

        <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>
          ROCKYRIDGE · DENTAL AI · v1
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
