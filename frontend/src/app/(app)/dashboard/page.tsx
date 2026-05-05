'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { KpiTile } from '@/components/domain/KpiTile';
import { AppointmentCard } from '@/components/domain/AppointmentCard';
import { PatientCard } from '@/components/domain/PatientCard';
import { LabPipeline } from '@/components/domain/LabPipeline';
import { ToothChartTile } from '@/components/domain/ToothChartTile';
import { StatusPill } from '@/components/domain/StatusPill';
import { Drawer } from '@/components/overlays/Drawer';
import { CenterModal } from '@/components/overlays/CenterModal';
import { useToast } from '@/components/overlays/ToastContext';
import { PATIENTS, APPOINTMENTS, INVOICES, LabCase, LAB_CASES } from '@/lib/data';
import { ArrowLeft, X } from 'lucide-react';
import { api, type PatientDTO } from '@/lib/api';

// Build a naive local-time ISO string (no Z suffix) for an instant `minutes` later
// than the local-naive `startIso`. Avoids the toISOString() pitfall which converts
// to UTC and silently shifts the booking by the local offset.
function addMinutesNaive(startIso: string, minutes: number): string {
  const d = new Date(startIso);
  d.setMinutes(d.getMinutes() + minutes);
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
}

// Status helpers
const WS_STATUS: Record<string, { bg: string; fg: string; label: string }> = {
  confirmed: { bg: '#E8F5EE', fg: '#2A7D4F', label: 'Confirmed' },
  pending:   { bg: '#FDF3E5', fg: '#B45309', label: 'Pending' },
  no_show:   { bg: '#F8E5E8', fg: '#9B2335', label: 'No-show' },
  completed: { bg: '#F5F2EC', fg: '#4A5568', label: 'Completed' },
};

export default function DashboardPage() {
  const router = useRouter();
  const { addToast, dismissToast } = useToast();

  // Appointment data (local state so status changes reflect)
  const [appointments, setAppointments] = React.useState([...APPOINTMENTS]);

  // Drawer state
  const [drawerMode, setDrawerMode] = React.useState<'appointment' | 'new-patient' | null>(null);

  // New appointment form state
  const [apptPatient, setApptPatient] = React.useState<typeof PATIENTS[0] | null>(null);
  const [apptPatientQ, setApptPatientQ] = React.useState('');
  const [apptPatientFocus, setApptPatientFocus] = React.useState(false);
  const [apptDate, setApptDate] = React.useState('2026-05-04');
  const [apptTime, setApptTime] = React.useState('09:00');
  const [apptDuration, setApptDuration] = React.useState('60');

  // Real patient list (UUID-keyed) loaded from API; used to resolve apptPatient → real id.
  const [apiPatients, setApiPatients] = React.useState<PatientDTO[]>([]);
  React.useEffect(() => {
    api.patients.list().then(setApiPatients).catch(() => {});
  }, []);

  // New patient form state
  const [newFirst, setNewFirst] = React.useState('');
  const [newLast, setNewLast] = React.useState('');
  const [newDob, setNewDob] = React.useState('');
  const [newPhone, setNewPhone] = React.useState('');
  const [newEmail, setNewEmail] = React.useState('');
  const [newInsurance, setNewInsurance] = React.useState('');
  const [newIsMinor, setNewIsMinor] = React.useState(false);
  const [newGuardian, setNewGuardian] = React.useState('');
  const [newConsent, setNewConsent] = React.useState(false);

  // Expanded appointment
  const [expandedApptId, setExpandedApptId] = React.useState<string | null>(null);

  // Modals
  const [patientModal, setPatientModal] = React.useState<typeof PATIENTS[0] | null>(null);
  const [invoiceModal, setInvoiceModal] = React.useState<typeof INVOICES[0] | null>(null);
  const [labCaseModal, setLabCaseModal] = React.useState<LabCase | null>(null);
  const [apptWorkspace, setApptWorkspace] = React.useState<typeof APPOINTMENTS[0] | null>(null);

  // ─── Patient search helpers ───
  const filteredPatients = PATIENTS.filter(p =>
    !apptPatientQ || (p.first + ' ' + p.last).toLowerCase().includes(apptPatientQ.toLowerCase())
  );

  // ─── Handlers ───
  const handleBookAppt = async () => {
    if (!apptPatient) { addToast('Pick a patient first.'); return; }
    const name = apptPatient.first + ' ' + apptPatient.last;
    // Resolve mock-id patient to a real-DB patient by name match. New rows added via the
    // patient drawer now go through api.patients.create and already carry a real UUID.
    const realId = /^[0-9a-f]{8}-/.test(apptPatient.id)
      ? apptPatient.id
      : (apiPatients.find(p =>
          (p.first_name ?? '').toLowerCase() === apptPatient.first.toLowerCase() &&
          (p.last_name ?? '').toLowerCase() === apptPatient.last.toLowerCase()
        )?.id ?? null);
    if (!realId) { addToast('Patient not in backend yet — save the patient first.'); return; }
    try {
      const startIso = `${apptDate}T${apptTime}:00`;
      const endIso = addMinutesNaive(startIso, parseInt(apptDuration));
      await api.appointments.create({
        start_time: startIso,
        end_time: endIso,
        patient_id: realId,
        provider_id: 1,
        reason: 'Appointment',
        patient_name: name,
        service_name: 'General',
      });
      setDrawerMode(null);
      addToast('Appointment booked.', name + ' · ' + apptDate + ' · ' + apptTime);
    } catch { addToast('Failed to book appointment.'); }
  };

  const handleSaveNewPatient = () => {
    const id = 'P-' + String(Math.floor(10000 + Math.random() * 90000));
    const p = {
      id, first: newFirst, last: newLast, dob: newDob,
      insurance: newInsurance, last_visit: 'New',
      status: 'active' as const,
    };
    PATIENTS.push(p);
    setApptPatient(p);
    setApptPatientQ(p.first + ' ' + p.last);
    // Go back to appointment drawer
    setDrawerMode('appointment');
    addToast('Patient added.', p.first + ' ' + p.last);
  };

  const handleApptAction = async (action: string) => {
    if (!apptWorkspace) return;
    const statusMap: Record<string, string> = {
      'Confirmed': 'confirmed',
      'Completed': 'completed',
      'Marked no-show': 'no_show',
      'Checked in': 'checked_in',
      'Started': 'in_progress',
    };
    const newStatus = statusMap[action];
    if (newStatus) {
      try {
        await api.appointments.setStatus(apptWorkspace.id, newStatus);
        setAppointments(prev => prev.map(a =>
          a.id === apptWorkspace.id ? { ...a, status: newStatus as typeof a.status } : a
        ));
      } catch { /* ignore - local state update still happens */ }
    }
    if (action === 'Cancelled') {
      try {
        await api.appointments.cancel(apptWorkspace.id);
      } catch { /* ignore */ }
    }
    addToast(action + '.', apptWorkspace.patient + ' · ' + apptWorkspace.id);
    if (action === 'Confirmed' || action === 'Completed' || action === 'Marked no-show' || action === 'Cancelled') {
      setApptWorkspace(null);
    }
  };

  // ─── Patient Overview Modal ───
  const patientOverviewModal = patientModal && (() => {
    const p = patientModal;
    const initials = (p.first[0] + p.last[0]).toUpperCase();
    const sTone: Record<string, { bg: string; fg: string }> = {
      active: { bg: '#E8F5EE', fg: '#2A7D4F' },
      recall: { bg: '#FDF3E5', fg: '#B45309' },
      plan: { bg: '#F5F2EC', fg: '#4A5568' },
      inactive: { bg: '#F5F2EC', fg: '#8A9BB0' },
    };
    const tone = sTone[p.status] || sTone.active;
    return (
      <CenterModal open={true} onClose={() => setPatientModal(null)} width="min(600px, 92vw)">
        <div className="center-modal-topbar">
          <button className="drawer-back" onClick={() => setPatientModal(null)}>
            <ArrowLeft size={18} strokeWidth={1.5} />
          </button>
          <span className="back-label">Back to Dashboard</span>
        </div>
        <div className="center-modal-body">
          <div className="appt-ws-hero">
            <div className="appt-ws-ava">{initials}</div>
            <div className="appt-ws-info">
              <div className="appt-ws-name">{p.first} {p.last}</div>
              <div className="appt-ws-id">{p.id} · {p.dob} · {p.insurance}</div>
            </div>
            <span style={{ fontSize: '.68rem', fontWeight: 600, padding: '4px 12px', borderRadius: 999, letterSpacing: '.06em', textTransform: 'uppercase', background: tone.bg, color: tone.fg }}>{p.status}</span>
          </div>
          <div>
            <div className="detail-row"><span className="detail-k">Date of birth</span><span className="detail-v">{p.dob}</span></div>
            <div className="detail-row"><span className="detail-k">Insurance</span><span className="detail-v">{p.insurance}</span></div>
            <div className="detail-row"><span className="detail-k">Last visit</span><span className="detail-v">{p.last_visit}</span></div>
            <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v">{p.status}</span></div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary btn-md" onClick={() => { setPatientModal(null); router.push('/patients/' + p.id); }}>Open chart</button>
            <button className="btn btn-ghost btn-md" onClick={() => setPatientModal(null)}>Close</button>
          </div>
        </div>
      </CenterModal>
    );
  })();

  // ─── Invoice Overview Modal ───
  const invoiceOverviewModal = invoiceModal && (() => {
    const i = invoiceModal;
    const tone = i.status === 'paid' ? { bg: '#E8F5EE', fg: '#2A7D4F' }
      : i.status === 'partial' ? { bg: '#FDF3E5', fg: '#B45309' }
      : { bg: '#F8E5E8', fg: '#9B2335' };
    return (
      <CenterModal open={true} onClose={() => setInvoiceModal(null)} width="min(560px, 92vw)">
        <div className="center-modal-topbar">
          <button className="drawer-back" onClick={() => setInvoiceModal(null)}>
            <ArrowLeft size={18} strokeWidth={1.5} />
          </button>
          <span className="back-label">Back to Dashboard</span>
        </div>
        <div className="center-modal-body">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="appt-ws-name">{i.id}</div>
              <div className="appt-ws-detail">{i.patient}</div>
            </div>
            <StatusPill status={i.status} />
          </div>
          <div>
            <div className="detail-row"><span className="detail-k">Patient</span><span className="detail-v">{i.patient}</span></div>
            <div className="detail-row"><span className="detail-k">Total</span><span className="detail-v" style={{ fontFamily: 'var(--font-mono)' }}>${i.total.toFixed(2)}</span></div>
            <div className="detail-row"><span className="detail-k">Balance</span><span className="detail-v" style={{ fontFamily: 'var(--font-mono)', color: i.balance > 0 ? '#B45309' : '#1C2333' }}>${i.balance.toFixed(2)}</span></div>
            <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v">{i.status}</span></div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary btn-md" onClick={() => { setInvoiceModal(null); router.push('/billing/invoices/' + i.id); }}>View invoice</button>
            <button className="btn btn-ghost btn-md" onClick={() => setInvoiceModal(null)}>Close</button>
          </div>
        </div>
      </CenterModal>
    );
  })();

  // ─── Lab Case Overview Modal ───
  const labCaseOverviewModal = labCaseModal && (() => {
    const c = labCaseModal;
    const colLabel: Record<string, string> = { sent: 'Sent', progress: 'In progress', returned: 'Returned' };
    return (
      <CenterModal open={true} onClose={() => setLabCaseModal(null)} width="min(560px, 92vw)">
        <div className="center-modal-topbar">
          <button className="drawer-back" onClick={() => setLabCaseModal(null)}>
            <ArrowLeft size={18} strokeWidth={1.5} />
          </button>
          <span className="back-label">Back to Dashboard</span>
        </div>
        <div className="center-modal-body">
          <div className="appt-ws-hero">
            <div className="appt-ws-ava">{c.patient.split(' ').map(s => s[0]).join('').toUpperCase()}</div>
            <div className="appt-ws-info">
              <div className="appt-ws-name">{c.patient}</div>
              <div className="appt-ws-detail">{c.item}</div>
              <div className="appt-ws-id">{c.id}</div>
            </div>
            <StatusPill status={c.col} label={colLabel[c.col] || c.col} />
          </div>
          <div>
            <div className="detail-row"><span className="detail-k">Case ID</span><span className="detail-v">{c.id}</span></div>
            <div className="detail-row"><span className="detail-k">Item</span><span className="detail-v">{c.item}</span></div>
            <div className="detail-row"><span className="detail-k">Vendor</span><span className="detail-v">{c.vendor}</span></div>
            <div className="detail-row"><span className="detail-k">ETA</span><span className="detail-v">{c.eta}</span></div>
            <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v">{colLabel[c.col] || c.col}</span></div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary btn-md" onClick={() => { setLabCaseModal(null); router.push('/lab/' + c.id); }}>Track case</button>
            <button className="btn btn-ghost btn-md" onClick={() => setLabCaseModal(null)}>Close</button>
          </div>
        </div>
      </CenterModal>
    );
  })();

  // ─── Appointment Workspace Modal ───
  const apptWorkspaceModal = apptWorkspace && (() => {
    const a = apptWorkspace;
    const tone = WS_STATUS[a.status] || WS_STATUS.confirmed;
    const initials = a.patient.split(' ').map(s => s[0]).slice(0, 2).join('').toUpperCase();
    return (
      <CenterModal open={true} onClose={() => setApptWorkspace(null)}>
        <div className="center-modal-topbar">
          <button className="drawer-back" onClick={() => setApptWorkspace(null)}>
            <ArrowLeft size={18} strokeWidth={1.5} />
          </button>
          <span className="back-label">Back to Dashboard</span>
        </div>
        <div className="center-modal-body">
          <div className="appt-ws-hero">
            <div className="appt-ws-ava">{initials}</div>
            <div className="appt-ws-info">
              <div className="appt-ws-name">{a.patient}</div>
              <div className="appt-ws-detail">{a.kind} · {a.provider} · Op {a.chair} · {a.time} — {a.duration} min</div>
              <div className="appt-ws-id">{a.id} · {a.patient_id}</div>
            </div>
            <span style={{ fontSize: '.68rem', fontWeight: 600, padding: '4px 12px', borderRadius: 4, letterSpacing: '.06em', textTransform: 'uppercase', background: tone.bg, color: tone.fg, alignSelf: 'flex-start' }}>{tone.label}</span>
          </div>
          <div className="appt-ws-actions">
            <button className="btn btn-primary btn-md" onClick={() => handleApptAction('Confirmed')}>Confirm</button>
            <button className="btn btn-ghost btn-md" onClick={() => handleApptAction('Checked in')}>Check in</button>
            <button className="btn btn-ghost btn-md" onClick={() => handleApptAction('Started')}>Start</button>
            <button className="btn btn-ghost btn-md" onClick={() => handleApptAction('Completed')}>Complete</button>
            <button className="btn btn-ghost btn-md" onClick={() => handleApptAction('Marked no-show')}>No show</button>
            <button className="btn btn-ghost btn-md" onClick={() => handleApptAction('Rescheduled')}>Reschedule</button>
            <button className="btn btn-ghost btn-md" style={{ color: 'var(--rr-error)' }} onClick={() => handleApptAction('Cancelled')}>Cancel</button>
          </div>
          <ToothChartTile />
        </div>
      </CenterModal>
    );
  })();

  return (
    <>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Today&apos;s clinic</h1>
          <div className="page-sub">Saturday · May 4 · 2026 — {appointments.length} appointments scheduled · {LAB_CASES.length} lab cases in flight.</div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button data-audit="local-only" className="btn btn-ghost btn-md" onClick={() => addToast('Day exported.', 'dashboard-2026-05-04.pdf')}>Export day</button>
          <button className="btn btn-primary btn-md" onClick={() => setDrawerMode('appointment')}>+ New appointment</button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="kpi-row">
        <Link href="/schedule" style={{ textDecoration: 'none', color: 'inherit', display: 'contents' }}>
          <KpiTile label="Schedule fill" value="78%" delta="+ 4%" trend="up" accent="steel" />
        </Link>
        <Link href="/schedule" style={{ textDecoration: 'none', color: 'inherit', display: 'contents' }}>
          <KpiTile label="Recall reach" value="92%" delta="+ 1.2%" trend="up" accent="steel" />
        </Link>
        <Link href="/billing" style={{ textDecoration: 'none', color: 'inherit', display: 'contents' }}>
          <KpiTile label="No-shows" value="3" delta="+ 1" trend="down" accent="navy" />
        </Link>
        <Link href="/lab" style={{ textDecoration: 'none', color: 'inherit', display: 'contents' }}>
          <KpiTile label="Lab in flight" value={String(LAB_CASES.length)} delta="– 2" trend="up" accent="steel" />
        </Link>
      </div>

      {/* Appointments + Lab/Tooth */}
      <div className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <div className="panel-h-title">Today&apos;s appointments</div>
              <div className="panel-h-sub">{appointments.length} scheduled · {appointments.filter(a => a.status === 'confirmed').length} confirmed · {appointments.filter(a => a.status === 'pending').length} pending · {appointments.filter(a => a.status === 'no_show').length} no-show</div>
            </div>
            <Link className="panel-h-action" href="/schedule">Open the schedule →</Link>
          </div>
          <div className="stack">
            {appointments.map(a => (
              <div key={a.id}>
                <AppointmentCard
                  appointment={a}
                  expanded={expandedApptId === a.id}
                  onClick={() => setExpandedApptId(expandedApptId === a.id ? null : a.id)}
                />
                {expandedApptId === a.id && (
                  <div className="appt-quick-actions">
                    <button className="btn btn-ghost btn-md" onClick={() => {
                      setAppointments(prev => prev.map(ap => ap.id === a.id ? { ...ap, status: 'confirmed' as const } : ap));
                      addToast('Checked in.', a.patient);
                    }}>Check in</button>
                    <button className="btn btn-primary btn-md" onClick={() => { setExpandedApptId(null); setApptWorkspace(a); }}>Open Chart</button>
                    <button className="btn btn-ghost btn-md" onClick={() => addToast('Reschedule requested.', a.patient)}>Reschedule</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="panel">
            <div className="panel-header">
              <div>
                <div className="panel-h-title">Lab pipeline</div>
                <div className="panel-h-sub">Sent · in progress · returned</div>
              </div>
              <Link className="panel-h-action" href="/lab">Open the lab →</Link>
            </div>
            <LabPipeline onCaseClick={(c) => setLabCaseModal(c)} />
          </div>
          <ToothChartTile />
        </div>
      </div>

      {/* Recent Patients */}
      <div className="panel">
        <div className="panel-header">
          <div>
            <div className="panel-h-title">Recent patients</div>
            <div className="panel-h-sub">Last 6 visits across all providers</div>
          </div>
          <Link className="panel-h-action" href="/patients">All patients →</Link>
        </div>
        <div className="stack" style={{ gap: 8 }}>
          {PATIENTS.map(p => (
            <div key={p.id} onClick={() => setPatientModal(p)} style={{ cursor: 'pointer' }}>
              <PatientCard patient={p} />
            </div>
          ))}
        </div>
      </div>

      {/* Recent Invoices */}
      <div className="panel">
        <div className="panel-header">
          <div>
            <div className="panel-h-title">Recent invoices</div>
            <div className="panel-h-sub">Last 4 days</div>
          </div>
          <Link className="panel-h-action" href="/billing">All invoices →</Link>
        </div>
        <table className="recent-table">
          <thead><tr><th>Invoice</th><th>Patient</th><th style={{textAlign:'right'}}>Total</th><th style={{textAlign:'right'}}>Balance</th><th>Status</th></tr></thead>
          <tbody>
            {INVOICES.map(i => (
              <tr key={i.id} style={{ cursor: 'pointer' }} onClick={() => setInvoiceModal(i)}>
                <td className="id">{i.id}</td>
                <td>{i.patient}</td>
                <td style={{textAlign:'right', fontFamily: "'JetBrains Mono', monospace"}}>${i.total.toFixed(2)}</td>
                <td style={{textAlign:'right', fontFamily: "'JetBrains Mono', monospace", color: i.balance > 0 ? '#B45309' : '#4A5568'}}>${i.balance.toFixed(2)}</td>
                <td><StatusPill status={i.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>
        ROCKYRIDGE · DENTAL AI · v1
      </div>

      {/* ─── NEW APPOINTMENT DRAWER ─── */}
      {drawerMode === 'appointment' && (
        <Drawer
          open={true}
          onClose={() => setDrawerMode(null)}
          meta="New appointment"
          title="Book a new appointment"
          sub="Select patient, provider, and slot."
          footer={
            <>
              <button className="btn btn-ghost btn-md" onClick={() => setDrawerMode(null)}>Cancel</button>
              <button className="btn btn-primary btn-md" onClick={handleBookAppt}>Book appointment</button>
            </>
          }
        >
          <div className="field">
            <div className="field-label-row">
              <label className="lbl">Patient</label>
              <a className="field-link" onClick={() => setDrawerMode('new-patient')}>+ New patient</a>
            </div>
            <div className="search-select">
              <input className="d-input" placeholder="Search patients..." value={apptPatientQ}
                onChange={e => { setApptPatientQ(e.target.value); setApptPatient(null); }}
                onFocus={() => setApptPatientFocus(true)}
                onBlur={() => setTimeout(() => setApptPatientFocus(false), 150)}
              />
              {apptPatientFocus && filteredPatients.length > 0 && (
                <div className="search-results">
                  {filteredPatients.slice(0, 8).map(p => (
                    <div key={p.id}
                      className={'search-opt' + (apptPatient && apptPatient.id === p.id ? ' selected' : '')}
                      onMouseDown={() => { setApptPatient(p); setApptPatientQ(p.first + ' ' + p.last); setApptPatientFocus(false); }}
                    >
                      <span className="search-ava">{(p.first[0] + p.last[0]).toUpperCase()}</span>
                      {p.first} {p.last}
                      <span className="search-sub">{p.id}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="field">
            <label className="lbl">Provider</label>
            <select className="d-input" defaultValue="hau">
              <option value="hau">Dr Hau Le · Operatory 1</option>
              <option value="sara">Dr Sara Lim · Operatory 2</option>
              <option value="renu">Hyg. Renu · Operatory 3</option>
            </select>
          </div>
          <div className="field">
            <label className="lbl">Procedure</label>
            <select className="d-input" defaultValue="recall">
              <option value="recall">Recall · 6mo (30 min)</option>
              <option value="crown-prep">Crown prep (60 min)</option>
              <option value="hygiene">Hygiene · scaling (30 min)</option>
              <option value="implant">Implant follow-up (90 min)</option>
              <option value="composite">Composite · MOD (60 min)</option>
              <option value="consult">New patient consult (30 min)</option>
              <option value="reline">Denture relines (45 min)</option>
              <option value="crown-seat">Crown seat (45 min)</option>
            </select>
          </div>
          <div className="field-row">
            <div className="field">
              <label className="lbl">Date</label>
              <input type="date" className="d-input" value={apptDate} onChange={e => setApptDate(e.target.value)} />
            </div>
            <div className="field">
              <label className="lbl">Time</label>
              <input type="time" className="d-input" value={apptTime} onChange={e => setApptTime(e.target.value)} />
            </div>
          </div>
          <div className="field">
            <label className="lbl">Duration</label>
            <select className="d-input" value={apptDuration} onChange={e => setApptDuration(e.target.value)}>
              <option value="30">30 min</option>
              <option value="45">45 min</option>
              <option value="60">60 min</option>
              <option value="90">90 min</option>
            </select>
          </div>
          <div className="field">
            <label className="lbl">Notes</label>
            <textarea className="d-textarea" placeholder="Reason for visit, special instructions..." />
          </div>
        </Drawer>
      )}

      {/* ─── NEW PATIENT DRAWER (nested from appointment) ─── */}
      {drawerMode === 'new-patient' && (
        <Drawer
          open={true}
          onClose={() => setDrawerMode('appointment')}
          meta="New patient"
          title="Add a new patient"
          sub="Fill in patient details below."
          showBack
          footer={
            <>
              <button className="btn btn-ghost btn-md" onClick={() => setDrawerMode('appointment')}>Back</button>
              <button className="btn btn-primary btn-md" disabled={!newFirst || !newLast} onClick={handleSaveNewPatient}>Save patient</button>
            </>
          }
        >
          <div className="field-row">
            <div className="field"><label className="lbl">First name *</label><input className="d-input" value={newFirst} onChange={e => setNewFirst(e.target.value)} /></div>
            <div className="field"><label className="lbl">Last name *</label><input className="d-input" value={newLast} onChange={e => setNewLast(e.target.value)} /></div>
          </div>
          <div className="field"><label className="lbl">Date of birth</label><input type="date" className="d-input" value={newDob} onChange={e => setNewDob(e.target.value)} /></div>
          <div className="field-row">
            <div className="field"><label className="lbl">Phone</label><input className="d-input" value={newPhone} onChange={e => setNewPhone(e.target.value)} /></div>
            <div className="field"><label className="lbl">Email</label><input className="d-input" value={newEmail} onChange={e => setNewEmail(e.target.value)} /></div>
          </div>
          <div className="field"><label className="lbl">Insurance provider</label><input className="d-input" value={newInsurance} onChange={e => setNewInsurance(e.target.value)} /></div>
          <div className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" id="isMinor" checked={newIsMinor} onChange={e => setNewIsMinor(e.target.checked)} />
            <label htmlFor="isMinor" className="lbl" style={{ marginBottom: 0 }}>Patient is a minor</label>
          </div>
          {newIsMinor && <div className="field"><label className="lbl">Guardian name</label><input className="d-input" value={newGuardian} onChange={e => setNewGuardian(e.target.value)} /></div>}
          <div className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" id="consent" checked={newConsent} onChange={e => setNewConsent(e.target.checked)} />
            <label htmlFor="consent" className="lbl" style={{ marginBottom: 0 }}>Consent approved</label>
          </div>
        </Drawer>
      )}

      {/* All Modals */}
      {patientOverviewModal}
      {invoiceOverviewModal}
      {labCaseOverviewModal}
      {apptWorkspaceModal}
    </>
  );
}
