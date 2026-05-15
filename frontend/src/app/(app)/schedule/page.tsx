'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { APPOINTMENTS } from '@/lib/data';
import { StatusPill } from '@/components/domain/StatusPill';
import { Drawer } from '@/components/overlays/Drawer';
import { CenterModal } from '@/components/overlays/CenterModal';
import { useToast } from '@/components/overlays/ToastContext';
import { ArrowLeft } from 'lucide-react';
import { api, type PatientDTO, type BusyBlockDTO } from '@/lib/api';
import type { ScheduleEvent, BusyBlockBg } from '@/components/domain/ScheduleCalendar';
import { BusyBlocksDrawer } from '@/components/domain/BusyBlocksDrawer';
import { PatientPickerWithCreate } from '@/components/domain/PatientPickerWithCreate';
import { ConfirmDialog } from '@/components/overlays/ConfirmDialog';

// Calendar uses DOM APIs — load client-only.
const ScheduleCalendar = dynamic(() => import('@/components/domain/ScheduleCalendar'), { ssr: false });

// Anchor date (today per CLAUDE.md auto-memory). Mock APPOINTMENTS only carry HH:MM, so we
// place them on this date for the day/week view to be populated. Calendar nav still works
// across other days — they just have no seed events.
const ANCHOR_DATE = '2026-05-04'; // Monday

type ApptStatus = 'confirmed' | 'pending' | 'no_show' | 'completed' | 'cancelled';

interface AppointmentLocal {
  id: string;
  date: string;       // YYYY-MM-DD
  time: string;       // HH:MM
  duration: number;   // minutes
  patient: string;
  patient_id: string;
  provider: string;
  chair: string;
  kind: string;
  status: ApptStatus;
}

const SEED: AppointmentLocal[] = APPOINTMENTS.map(a => ({
  id: a.id,
  date: ANCHOR_DATE,
  time: a.time,
  duration: a.duration,
  patient: a.patient,
  patient_id: a.patient_id,
  provider: a.provider,
  chair: a.chair,
  kind: a.kind,
  status: a.status,
}));

const STATUSES: ApptStatus[] = ['confirmed', 'pending', 'completed', 'no_show'];

function toIso(date: string, time: string): string {
  // Build a local-time ISO string. We use a "naive" string with no tz suffix so FullCalendar
  // treats it as the user's local time, which matches how clinic schedules are read.
  return `${date}T${time}:00`;
}

function addMinutes(iso: string, minutes: number): string {
  const d = new Date(iso);
  d.setMinutes(d.getMinutes() + minutes);
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
}

function isoToDateTime(iso: Date): { date: string; time: string } {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return {
    date: `${iso.getFullYear()}-${pad(iso.getMonth() + 1)}-${pad(iso.getDate())}`,
    time: `${pad(iso.getHours())}:${pad(iso.getMinutes())}`,
  };
}

function diffMinutes(start: Date, end: Date): number {
  return Math.round((end.getTime() - start.getTime()) / 60000);
}

// Surface backend conflict messages — the create/reschedule endpoints return a
// 409 with a structured `detail` envelope ({ error, message, ... }). For the
// busy-block case the envelope also includes `busy_block.label` which we show
// inline so the user knows *why* it failed.
function reasonFromError(e: unknown, fallback: string): string {
  if (e && typeof e === 'object' && 'status' in e && 'body' in e) {
    const status = (e as { status: number }).status;
    const body = (e as { body: unknown }).body;
    if (status === 409 && body && typeof body === 'object') {
      const d = (body as { detail?: { error?: string; message?: string; busy_block?: { label?: string | null } } }).detail;
      if (d?.error === 'Provider busy') {
        const lbl = d.busy_block?.label;
        return lbl ? `Provider busy (${lbl}).` : 'Provider is on a busy block during that time.';
      }
      if (d?.error === 'Appointment conflict') return 'That slot already has an appointment.';
      if (d?.message) return d.message;
    }
  }
  return fallback;
}

// Map busy blocks (DB shape) to FullCalendar background events. Handles both
// recurring weekday rules (with optional `recurrence_until`) and single-date
// one-offs. DB weekday convention is 0=Mon..6=Sun; FullCalendar uses 0=Sun..6=Sat.
function pad2(n: number): string { return n.toString().padStart(2, '0'); }
function nextDayIso(ymd: string): string {
  // `endRecur` in FullCalendar is exclusive — add one day to the inclusive UI date.
  const d = new Date(ymd + 'T00:00:00');
  d.setDate(d.getDate() + 1);
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}
function busyToBg(blocks: BusyBlockDTO[]): BusyBlockBg[] {
  const out: BusyBlockBg[] = [];
  for (const b of blocks) {
    const startTime = `${pad2(b.start_hour)}:${pad2(b.start_minute)}:00`;
    const endTime = `${pad2(b.end_hour)}:${pad2(b.end_minute)}:00`;
    const label = b.label ?? undefined;
    if (b.specific_date) {
      out.push({
        id: `bb-${b.id}`,
        start: `${b.specific_date}T${startTime}`,
        end: `${b.specific_date}T${endTime}`,
        label,
      });
    } else if (b.weekdays && b.weekdays.length) {
      out.push({
        id: `bb-${b.id}`,
        daysOfWeek: b.weekdays.map(d => (d + 1) % 7),
        startTime,
        endTime,
        ...(b.recurrence_until ? { endRecur: nextDayIso(b.recurrence_until) } : {}),
        label,
      });
    }
  }
  return out;
}

export default function SchedulePage() {
  const { addToast } = useToast();
  const [appts, setAppts] = React.useState<AppointmentLocal[]>(SEED);

  // New-appointment drawer (also reused for drag-create with prefilled date/time)
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [draftDate, setDraftDate] = React.useState(ANCHOR_DATE);
  const [draftTime, setDraftTime] = React.useState('09:00');
  const [draftDuration, setDraftDuration] = React.useState(60);
  const [patientOptions, setPatientOptions] = React.useState<PatientDTO[]>([]);
  const [draftPatient, setDraftPatient] = React.useState<PatientDTO | null>(null);
  const [draftProvider, setDraftProvider] = React.useState('Dr Hau Le');
  const [draftKind, setDraftKind] = React.useState('Recall · 6mo');

  React.useEffect(() => {
    api.patients.list()
      .then(rows => setPatientOptions(rows))
      .catch(() => { /* leave empty; createAppointment will toast a useful error */ });
  }, []);

  // Live busy blocks (replaces the BUSY_BLOCKS mock at runtime; mock stays as a
  // typings/fallback reference). Reloaded by the BusyBlocksDrawer on every change.
  const [busyBlocks, setBusyBlocks] = React.useState<BusyBlockDTO[]>([]);
  const reloadBusyBlocks = React.useCallback(async () => {
    try { setBusyBlocks(await api.v2.scheduling.busyBlocks.list()); }
    catch { /* leave empty; the calendar just shows no tinted bands */ }
  }, []);
  React.useEffect(() => { void reloadBusyBlocks(); }, [reloadBusyBlocks]);

  const [busyDrawerOpen, setBusyDrawerOpen] = React.useState(false);

  const draftPatientName = draftPatient
    ? `${draftPatient.first_name ?? ''} ${draftPatient.last_name ?? ''}`.trim()
    : '';

  // Detail modal for clicked event
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const detailAppt = detailId ? appts.find(a => a.id === detailId) ?? null : null;
  const [cancelConfirmOpen, setCancelConfirmOpen] = React.useState(false);

  const events: ScheduleEvent[] = appts.map(a => ({
    id: a.id,
    title: `${a.patient} · ${a.kind}`,
    start: toIso(a.date, a.time),
    end: addMinutes(toIso(a.date, a.time), a.duration),
    status: a.status,
    patient: a.patient,
    kind: a.kind,
  }));

  const busy = busyToBg(busyBlocks);

  const openNewDrawer = (date?: string, time?: string, duration?: number) => {
    setDraftDate(date ?? ANCHOR_DATE);
    setDraftTime(time ?? '09:00');
    setDraftDuration(duration ?? 60);
    setDraftProvider('Dr Hau Le');
    setDraftKind('Recall · 6mo');
    setDrawerOpen(true);
  };

  const onCalendarSelect = (start: Date, end: Date) => {
    const { date, time } = isoToDateTime(start);
    const duration = Math.max(15, diffMinutes(start, end));
    openNewDrawer(date, time, duration);
  };

  const onCalendarEventClick = (id: string) => {
    setDetailId(id);
  };

  const onCalendarEventDrop = async (id: string, start: Date) => {
    const { date, time } = isoToDateTime(start);
    const appt = appts.find(a => a.id === id);
    if (!appt) return;
    try {
      const startIso = toIso(date, time);
      const endIso = addMinutes(startIso, appt.duration);
      await api.appointments.reschedule(id, {
        start_time: startIso,
        end_time: endIso,
        patient_id: appt.patient_id,
        provider_id: 1,
        reason: appt.kind,
        patient_name: appt.patient,
        service_name: appt.kind,
      });
      setAppts(prev => prev.map(a => (a.id === id ? { ...a, date, time } : a)));
      addToast(`Rescheduled to ${date} ${time}`, id);
    } catch (e) {
      addToast(reasonFromError(e, 'Failed to reschedule.'));
    }
  };

  const onCalendarEventResize = (id: string, start: Date, end: Date) => {
    const duration = Math.max(15, diffMinutes(start, end));
    setAppts(prev => prev.map(a => (a.id === id ? { ...a, duration } : a)));
    addToast(`Duration set to ${duration} min`, id);
  };

  const createAppointment = async () => {
    if (!draftPatient) { addToast('Pick a patient first.'); return; }
    try {
      const startIso = toIso(draftDate, draftTime);
      const endIso = addMinutes(startIso, draftDuration);
      const res = await api.appointments.create({
        start_time: startIso,
        end_time: endIso,
        patient_id: draftPatient.id,
        provider_id: 1,
        reason: draftKind,
        patient_name: draftPatientName,
        service_name: draftKind,
      }) as { appointment_id: string };
      const id = res.appointment_id;
      setAppts(prev => [...prev, {
        id,
        date: draftDate,
        time: draftTime,
        duration: draftDuration,
        patient: draftPatientName,
        patient_id: draftPatient.id,
        provider: draftProvider,
        chair: '1',
        kind: draftKind,
        status: 'pending',
      }]);
      setDrawerOpen(false);
      addToast('Appointment booked.', `${draftDate} · ${draftTime}`);
    } catch (e) {
      addToast(reasonFromError(e, 'Failed to book appointment.'));
    }
  };

  const updateStatus = async (status: ApptStatus) => {
    if (!detailAppt) return;
    try {
      await api.appointments.setStatus(detailAppt.id, status);
      setAppts(prev => prev.map(a => (a.id === detailAppt.id ? { ...a, status } : a)));
      addToast(`Status: ${status}`, detailAppt.id);
    } catch { addToast('Failed to update status.'); }
  };

  const confirmCancel = async () => {
    if (!detailAppt) return;
    try {
      await api.appointments.cancel(detailAppt.id);
      setAppts(prev => prev.map(a => (
        a.id === detailAppt.id ? { ...a, status: 'cancelled' as const } : a
      )));
      addToast('Appointment cancelled.', detailAppt.id);
      setCancelConfirmOpen(false);
      setDetailId(null);
    } catch {
      addToast('Failed to cancel appointment.');
      setCancelConfirmOpen(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Schedule</h1>
          <div className="page-sub">{appts.length} appointments · drag a slot to book · drag an event to reschedule · resize to change duration</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost btn-md" onClick={() => addToast('Schedule exported.')}>Export</button>
          <button className="btn btn-ghost btn-md" onClick={() => setBusyDrawerOpen(true)}>Manage busy blocks</button>
          <button className="btn btn-primary btn-md" onClick={() => openNewDrawer()}>+ New appointment</button>
        </div>
      </div>

      <div className="panel" style={{ padding: 16 }}>
        <ScheduleCalendar
          events={events}
          busy={busy}
          initialDate={ANCHOR_DATE}
          onSelect={onCalendarSelect}
          onEventClick={onCalendarEventClick}
          onEventDrop={onCalendarEventDrop}
          onEventResize={onCalendarEventResize}
        />
      </div>

      <div className="panel">
        <div className="panel-header"><div className="panel-h-title">Appointment List</div></div>
        <table className="list">
          <thead><tr><th>Time</th><th>Patient</th><th>Procedure</th><th>Provider</th><th>Chair</th><th>Status</th></tr></thead>
          <tbody>
            {appts.map(a => (
              <tr key={a.id} style={{ cursor: 'pointer' }} onClick={() => setDetailId(a.id)}>
                <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.82rem' }}>{a.time}</td>
                <td style={{ fontWeight: 600 }}>{a.patient}</td><td>{a.kind}</td><td>{a.provider}</td><td>Op {a.chair}</td>
                <td><StatusPill status={a.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* New appointment drawer (reused for drag-create) */}
      {drawerOpen && (
        <Drawer
          open={true}
          onClose={() => setDrawerOpen(false)}
          meta="New appointment"
          title="Book a new appointment"
          sub="Select patient, provider, and slot."
          footer={
            <>
              <button className="btn btn-ghost btn-md" onClick={() => setDrawerOpen(false)}>Cancel</button>
              <button className="btn btn-primary btn-md" onClick={createAppointment}>Book appointment</button>
            </>
          }
        >
          <PatientPickerWithCreate
            patients={patientOptions}
            value={draftPatient}
            onChange={setDraftPatient}
            onCreated={(p) => setPatientOptions(prev => [...prev, p])}
          />
          <div className="field">
            <label className="lbl">Provider</label>
            <select className="d-input" value={draftProvider} onChange={e => setDraftProvider(e.target.value)}>
              <option value="Dr Hau Le">Dr Hau Le · Op 1</option>
              <option value="Dr Sara Lim">Dr Sara Lim · Op 2</option>
              <option value="Hyg. Renu">Hyg. Renu · Op 3</option>
            </select>
          </div>
          <div className="field">
            <label className="lbl">Procedure</label>
            <select className="d-input" value={draftKind} onChange={e => setDraftKind(e.target.value)}>
              <option>Recall · 6mo</option>
              <option>Crown prep · #36</option>
              <option>Hygiene · scaling</option>
              <option>Implant follow-up</option>
              <option>New patient consult</option>
            </select>
          </div>
          <div className="field-row">
            <div className="field"><label className="lbl">Date</label><input type="date" className="d-input" value={draftDate} onChange={e => setDraftDate(e.target.value)} /></div>
            <div className="field"><label className="lbl">Time</label><input type="time" className="d-input" value={draftTime} onChange={e => setDraftTime(e.target.value)} /></div>
          </div>
          <div className="field">
            <label className="lbl">Duration</label>
            <select className="d-input" value={String(draftDuration)} onChange={e => setDraftDuration(Number(e.target.value))}>
              <option value="30">30 min</option>
              <option value="45">45 min</option>
              <option value="60">60 min</option>
              <option value="90">90 min</option>
            </select>
          </div>
        </Drawer>
      )}

      {/* Detail modal — appointment overview + status actions */}
      {detailAppt && (
        <CenterModal open={true} onClose={() => setDetailId(null)} width="min(560px, 92vw)">
          <div className="center-modal-topbar"><button className="drawer-back" onClick={() => setDetailId(null)}><ArrowLeft size={18} strokeWidth={1.5} /></button><span className="back-label">Back to Schedule</span></div>
          <div className="center-modal-body">
            <div className="appt-ws-hero">
              <div className="appt-ws-ava">{detailAppt.patient.split(' ').map(s => s[0]).join('').toUpperCase()}</div>
              <div className="appt-ws-info">
                <div className="appt-ws-name">{detailAppt.patient}</div>
                <div className="appt-ws-detail">{detailAppt.kind}</div>
                <div className="appt-ws-id">{detailAppt.id} · {detailAppt.date} · {detailAppt.time} · {detailAppt.duration} min</div>
              </div>
              <StatusPill status={detailAppt.status} />
            </div>

            <div>
              <div className="detail-row"><span className="detail-k">Patient</span><span className="detail-v">{detailAppt.patient}</span></div>
              <div className="detail-row"><span className="detail-k">Provider</span><span className="detail-v">{detailAppt.provider}</span></div>
              <div className="detail-row"><span className="detail-k">Procedure</span><span className="detail-v">{detailAppt.kind}</span></div>
              <div className="detail-row"><span className="detail-k">Date</span><span className="detail-v">{detailAppt.date}</span></div>
              <div className="detail-row"><span className="detail-k">Time</span><span className="detail-v">{detailAppt.time}</span></div>
              <div className="detail-row"><span className="detail-k">Duration</span><span className="detail-v">{detailAppt.duration} min</span></div>
              <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v">{detailAppt.status}</span></div>
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {STATUSES.map(s => (
                <button key={s} className={'btn btn-md ' + (detailAppt.status === s ? 'btn-primary' : 'btn-ghost')} onClick={() => updateStatus(s)}>{s.replace('_', ' ')}</button>
              ))}
              <button
                className="btn btn-md btn-destructive"
                onClick={() => setCancelConfirmOpen(true)}
                disabled={detailAppt.status === 'cancelled'}
              >
                {detailAppt.status === 'cancelled' ? 'Cancelled' : 'Cancel appt'}
              </button>
            </div>
          </div>
        </CenterModal>
      )}

      <BusyBlocksDrawer
        open={busyDrawerOpen}
        onClose={() => setBusyDrawerOpen(false)}
        onChanged={reloadBusyBlocks}
      />

      <ConfirmDialog
        open={cancelConfirmOpen && !!detailAppt}
        onClose={() => setCancelConfirmOpen(false)}
        onConfirm={confirmCancel}
        destructive
        title="Cancel this appointment?"
        body={detailAppt
          ? `Cancel ${detailAppt.patient}'s appointment on ${detailAppt.date} at ${detailAppt.time}? You can re-book the slot afterwards.`
          : ''}
        confirmLabel="Cancel appointment"
        cancelLabel="Keep it"
      />
    </>
  );
}
