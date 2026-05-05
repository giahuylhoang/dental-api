'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { PATIENTS, APPOINTMENTS, INVOICES, type Patient } from '@/lib/data';
import { StatusPill } from '@/components/domain/StatusPill';
import { EmptyState } from '@/components/domain/EmptyState';
import { ToothChartTile } from '@/components/domain/ToothChartTile';
import { Drawer } from '@/components/overlays/Drawer';
import { useToast } from '@/components/overlays/ToastContext';
import { api, ApiError } from '@/lib/api';

const TABS = ['Overview','Tooth chart','Insurance','Documents','Notes','Treatment plans','Communications','Billing','Audit'];
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === '1';

export default function PatientDetailPage() {
  const params = useParams();
  const patientId = String(params.id ?? '');
  const mockPatient = PATIENTS.find(p => p.id === patientId);
  const [patient, setPatient] = React.useState<Patient | null>(mockPatient ?? null);
  const [loading, setLoading] = React.useState<boolean>(!USE_MOCKS && !mockPatient);
  const [tab, setTab] = React.useState(0);

  React.useEffect(() => {
    if (USE_MOCKS) { setPatient(mockPatient ?? null); return; }
    let cancelled = false;
    setLoading(true);
    api.patients.get(patientId)
      .then(r => {
        if (cancelled) return;
        setPatient({
          id: r.id,
          first: r.first_name ?? '',
          last: r.last_name ?? '',
          dob: '',
          insurance: '',
          last_visit: '',
          status: 'active',
        });
      })
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 404) {
          setPatient(null);
        } else if (mockPatient) {
          setPatient(mockPatient);
        } else {
          setPatient(null);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [patientId]);
  const [scheduleOpen, setScheduleOpen] = React.useState(false);
  const [apptDate, setApptDate] = React.useState('2026-05-05');
  const [apptTime, setApptTime] = React.useState('09:00');
  const [apptDuration, setApptDuration] = React.useState('60');
  const { addToast } = useToast();

  const handleBookAppt = async () => {
    if (!patient) return;
    const fullName = `${patient.first} ${patient.last}`;
    try {
      const startIso = `${apptDate}T${apptTime}:00`;
      // Use a naive-local end stamp so the duration matches what the user picked.
      // Going through .toISOString() converts to UTC and silently shifts the booking
      // by the local offset (start stays local, end becomes UTC) — the slot ends up wrong.
      const d = new Date(startIso);
      d.setMinutes(d.getMinutes() + parseInt(apptDuration));
      const pad = (n: number) => n.toString().padStart(2, '0');
      const endIso = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
      await api.appointments.create({
        start_time: startIso,
        end_time: endIso,
        patient_id: patient.id,
        provider_id: 1,
        reason: 'Appointment',
        patient_name: fullName,
        service_name: 'General',
      });
      setScheduleOpen(false);
      addToast('Appointment booked.', fullName + ' · ' + apptDate + ' · ' + apptTime);
    } catch { addToast('Failed to book appointment.'); }
  };

  const handleNewInvoice = async () => {
    if (!patient) return;
    try {
      const res = await api.v2.billing.invoices.create({
        patient_id: patient.id,
        lines: [{ procedure_code: 'E04', description: 'Exam', qty: 1, unit_price: 145 }],
      }) as { id: string };
      addToast('Invoice created.', res.id);
    } catch { addToast('Failed to create invoice.'); }
  };

  if (loading && !patient) return <EmptyState title="Loading…" description="Fetching patient record." />;
  if (!patient) return <EmptyState title="Patient not found" description="No patient matches this ID." />;

  const fullName = `${patient.first} ${patient.last}`;
  const initials = ((patient.first[0] ?? '?') + (patient.last[0] ?? '?')).toUpperCase();
  const patientAge = patient.dob ? Math.floor((Date.now() - new Date(patient.dob).getTime()) / 31557600000) : null;
  const patientAppts = APPOINTMENTS.filter(a => a.patient_id === patient.id);

  return (
    <>
      <style>{`
        .tab-bar{display:flex;gap:0;border-bottom:1px solid var(--rr-parchment);overflow-x:auto}
        .tab-btn{background:none;border:none;border-bottom:2px solid transparent;padding:10px 16px;font-family:var(--font-ui);font-size:.82rem;font-weight:500;color:var(--rr-slate-dark);cursor:pointer;white-space:nowrap}
        .tab-btn.active{color:hsl(var(--primary));border-bottom-color:hsl(var(--primary));font-weight:600}
      `}</style>

      {/* Header Panel */}
      <div className="panel" style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <div style={{ width: 64, height: 64, borderRadius: 999, background: 'hsl(var(--primary))', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.4rem', flexShrink: 0 }}>{initials}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.5rem', color: 'var(--rr-navy-800)', letterSpacing: '-.02em' }}>{fullName}</div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 4, flexWrap: 'wrap' }}>
            <span className="id-cell">{patient.id}</span>
            {patient.dob && <span style={{ fontFamily: 'var(--font-ui)', fontSize: '.82rem', color: 'var(--rr-slate-dark)' }}>DOB {patient.dob}{patientAge != null && ` · Age ${patientAge}`}</span>}
            {patient.insurance && <span className="pill" style={{ background: '#D9EAF5', color: '#2E6494' }}>{patient.insurance}</span>}
            <StatusPill status={patient.status} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setScheduleOpen(true)}>Schedule</button>
          <button className="btn btn-ghost btn-sm" onClick={handleNewInvoice}>New invoice</button>
          <button className="btn btn-primary btn-sm">Edit</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="panel" style={{ padding: 0 }}>
        <div className="tab-bar" style={{ padding: '0 24px' }}>
          {TABS.map((t, i) => (
            <button key={t} className={'tab-btn' + (tab === i ? ' active' : '')} onClick={() => setTab(i)}>{t}</button>
          ))}
        </div>
        <div style={{ padding: '24px' }}>
          {tab === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <div>
                <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--rr-slate-dark)', marginBottom: 8 }}>Medical flags</div>
                <span className="flag-chip" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 999, background: '#F8E5E8', color: '#9B2335', fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 600, marginRight: 6 }}>Bisphosphonates</span>
                <span className="flag-chip" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 999, background: '#F8E5E8', color: '#9B2335', fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 600, marginRight: 6 }}>Allergy: Penicillin</span>
                <span className="pill" style={{ background: '#FDF3E5', color: '#B45309', marginRight: 6 }}>Metformin</span>
              </div>
              <div>
                <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--rr-slate-dark)', marginBottom: 8 }}>Recent appointments</div>
                <table className="list">
                  <thead><tr><th>Date</th><th>Provider</th><th>Service</th><th>Status</th></tr></thead>
                  <tbody>
                    {patientAppts.length > 0 ? patientAppts.slice(0, 3).map((a, i) => (
                      <tr key={i}>
                        <td className="id-cell">2026-{['04-30','02-14','01-08'][i] || '01-01'}</td>
                        <td>{a.provider}</td><td>{a.kind}</td><td><StatusPill status={a.status} /></td>
                      </tr>
                    )) : <tr><td colSpan={4} style={{ color: '#8A9BB0', textAlign: 'center', padding: 20 }}>No appointments recorded.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {tab === 1 && <ToothChartTile />}
          {tab === 2 && (
            <table className="list">
              <thead><tr><th>Carrier</th><th>Policy #</th><th>Group</th><th>Holder</th><th>Coverage</th></tr></thead>
              <tbody><tr><td>{patient.insurance}</td><td className="id-cell">POL-{patient.id}-01</td><td className="id-cell">GRP-4421</td><td>{fullName}</td><td>{[['Basic','80%'],['Major','50%'],['Ortho','0%']].map(([k,v]) => <span key={k} className="pill" style={{background:'var(--rr-mist)',color:'var(--rr-steel-700)',marginRight:4}}>{k}: {v}</span>)}</td></tr></tbody>
            </table>
          )}
          {tab === 3 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              {[['xray','Panoramic 2026-01-10','2.4 MB'],['photo','Intraoral photo','1.1 MB'],['consent','Treatment consent','84 KB']].map(([kind,name,size]) => (
                <div key={name} style={{ border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: '14px 16px' }}>
                  <span className="pill" style={{ background: 'var(--rr-mist)', color: 'var(--rr-steel-700)', marginBottom: 8, display: 'inline-block' }}>{kind}</span>
                  <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.85rem', color: 'var(--rr-navy-800)', fontWeight: 500 }}>{name}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '.72rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>{size}</div>
                </div>
              ))}
            </div>
          )}
          {tab === 4 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[{ date: '2026-04-30', s: 'Pt reports mild sensitivity upper left.', o: 'Caries #14 confirmed on BW.', a: 'Caries #14.', p: 'Restore with amalgam.', locked: true }].map((n, i) => (
                <div key={i} style={{ border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: '14px 16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}><span className="id-cell">{n.date}</span>{n.locked && <span className="pill" style={{ background: '#F5F2EC', color: '#4A5568' }}>Locked</span>}</div>
                  {[['S',n.s],['O',n.o],['A',n.a],['P',n.p]].map(([k,v]) => (
                    <div key={k} style={{ display: 'flex', gap: 8, marginBottom: 4 }}><span style={{ fontFamily: 'var(--font-mono)', fontSize: '.76rem', fontWeight: 600, color: 'hsl(var(--primary))', width: 14 }}>{k}</span><span style={{ fontFamily: 'var(--font-ui)', fontSize: '.85rem', color: 'var(--rr-ink)' }}>{v}</span></div>
                  ))}
                </div>
              ))}
            </div>
          )}
          {tab === 5 && (
            <div>
              <Link href="/treatment" className="btn btn-ghost btn-sm" style={{ marginBottom: 14, display: 'inline-block', textDecoration: 'none' }}>Open in editor</Link>
              <table className="list">
                <thead><tr><th>Plan ID</th><th>Total</th><th>Status</th><th>Presented</th></tr></thead>
                <tbody><tr><td className="id-cell">TP-001</td><td className="num" style={{ fontFamily: 'var(--font-mono)', fontSize: '.82rem' }}>$3,200.00</td><td><span className="pill" style={{ background: '#E8F5EE', color: '#2A7D4F' }}>Accepted</span></td><td className="id-cell">2026-04-15</td></tr></tbody>
              </table>
            </div>
          )}
          {tab === 6 && <EmptyState title="No communications" description="No messages for this patient yet." />}
          {tab === 7 && (
            <table className="list">
              <thead><tr><th>Invoice</th><th>Total</th><th>Balance</th><th>Status</th></tr></thead>
              <tbody><tr><td><Link href="/billing/invoices/INV-2026-0872" className="id-cell" style={{ color: 'hsl(var(--primary))', textDecoration: 'none' }}>INV-2026-0872</Link></td><td className="num" style={{ fontFamily: 'var(--font-mono)', fontSize: '.82rem' }}>$420.00</td><td className="num" style={{ fontFamily: 'var(--font-mono)', fontSize: '.82rem' }}>$0.00</td><td><span className="pill" style={{ background: '#E8F5EE', color: '#2A7D4F' }}>Paid</span></td></tr></tbody>
            </table>
          )}
          {tab === 8 && (
            <table className="list">
              <thead><tr><th>Action</th><th>Entity</th><th>User</th><th>When</th></tr></thead>
              <tbody><tr><td><span className="pill" style={{ background: '#F5F2EC', color: '#4A5568' }}>UPDATE</span></td><td>Patient record</td><td>Hau Le</td><td className="id-cell">2026-05-02 14:32</td></tr></tbody>
            </table>
          )}
        </div>
      </div>

      <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>ROCKYRIDGE · DENTAL AI · v1</div>

      {/* Schedule Drawer */}
      {scheduleOpen && (
        <Drawer open={true} onClose={() => setScheduleOpen(false)} meta="Book appointment" title={`Book for ${fullName}`} sub="Select provider and time."
          footer={<><button className="btn btn-ghost btn-md" onClick={() => setScheduleOpen(false)}>Cancel</button><button className="btn btn-primary btn-md" onClick={handleBookAppt}>Book appointment</button></>}
        >
          <div className="field"><label className="lbl">Patient</label><input className="d-input" value={fullName} readOnly /></div>
          <div className="field"><label className="lbl">Provider</label>
            <select className="d-input" defaultValue="hau"><option value="hau">Dr Hau Le · Operatory 1</option><option value="sara">Dr Sara Lim · Operatory 2</option><option value="renu">Hyg. Renu · Operatory 3</option></select>
          </div>
          <div className="field"><label className="lbl">Procedure</label>
            <select className="d-input" defaultValue="recall"><option value="recall">Recall · 6mo (30 min)</option><option value="crown">Crown prep (60 min)</option><option value="hygiene">Hygiene · scaling (30 min)</option><option value="implant">Implant follow-up (90 min)</option></select>
          </div>
          <div className="field-row">
            <div className="field"><label className="lbl">Date</label><input type="date" className="d-input" value={apptDate} onChange={e => setApptDate(e.target.value)} /></div>
            <div className="field"><label className="lbl">Time</label><input type="time" className="d-input" value={apptTime} onChange={e => setApptTime(e.target.value)} /></div>
          </div>
          <div className="field"><label className="lbl">Duration</label>
            <select className="d-input" value={apptDuration} onChange={e => setApptDuration(e.target.value)}><option value="30">30 min</option><option value="45">45 min</option><option value="60">60 min</option><option value="90">90 min</option></select>
          </div>
        </Drawer>
      )}
    </>
  );
}
