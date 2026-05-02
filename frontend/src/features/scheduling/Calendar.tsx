import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import AppointmentDrawer from './AppointmentDrawer';
import { APPT_STATUSES, statusColor, statusLabel, type ApptStatus } from './appt-status';

interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: number;
  start_time: string;
  end_time: string;
  status: string;
  service_id: number;
  operatory_id?: string;
}

interface DragState {
  appt: Appointment;
  newStart: string;
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function weekDays(anchor: Date): Date[] {
  const days: Date[] = [];
  const start = new Date(anchor);
  start.setDate(anchor.getDate() - anchor.getDay());
  for (let i = 0; i < 7; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    days.push(d);
  }
  return days;
}

function apptStatusColor(status: string): string {
  return statusColor(status.toUpperCase() as ApptStatus);
}

export default function Calendar() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [anchor, setAnchor] = useState(() => new Date());
  const [pending, setPending] = useState<DragState | null>(null);
  const [conflictMsg, setConflictMsg] = useState<string | null>(null);
  const [drawerApptId, setDrawerApptId] = useState<string | null>(null);

  const days = weekDays(anchor);
  const weekStart = formatDate(days[0]);
  const weekEnd = formatDate(days[6]);

  const { data: appointments = [] } = useQuery<Appointment[]>({
    queryKey: ['appointments', clinicId, weekStart],
    queryFn: () =>
      fetcher<Appointment[]>(
        `/api/appointments?start=${weekStart}&end=${weekEnd}`,
      ),
  });

  const reschedule = useMutation({
    mutationFn: ({ id, start_time, end_time }: { id: string; start_time: string; end_time: string }) =>
      fetcher(`/api/appointments/${id}/reschedule`, {
        method: 'PUT',
        body: JSON.stringify({ start_time, end_time }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointments', clinicId] });
      setPending(null);
    },
    onError: (err: Error) => {
      if (err.message.includes('409') || err.message.toLowerCase().includes('conflict')) {
        setConflictMsg(err.message);
      }
      setPending(null);
    },
  });

  function confirmReschedule() {
    if (!pending) return;
    const orig = pending.appt;
    const origDuration =
      new Date(orig.end_time).getTime() - new Date(orig.start_time).getTime();
    const newStart = new Date(pending.newStart);
    const newEnd = new Date(newStart.getTime() + origDuration);
    reschedule.mutate({
      id: orig.id,
      start_time: newStart.toISOString(),
      end_time: newEnd.toISOString(),
    });
  }

  const hours = Array.from({ length: 10 }, (_, i) => i + 8); // 08:00–17:00

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          className="rounded border px-3 py-1 text-sm hover:bg-zinc-100"
          onClick={() => {
            const d = new Date(anchor);
            d.setDate(d.getDate() - 7);
            setAnchor(d);
          }}
        >
          ← Prev
        </button>
        <span className="text-sm font-medium">
          {days[0].toLocaleDateString('en-CA')} – {days[6].toLocaleDateString('en-CA')}
        </span>
        <button
          className="rounded border px-3 py-1 text-sm hover:bg-zinc-100"
          onClick={() => {
            const d = new Date(anchor);
            d.setDate(d.getDate() + 7);
            setAnchor(d);
          }}
        >
          Next →
        </button>
        {/* Status legend */}
        <div className="ml-auto flex flex-wrap gap-1">
          {APPT_STATUSES.map((s) => (
            <span key={s} className={`rounded px-2 py-0.5 text-xs font-medium ${statusColor(s)}`}>
              {statusLabel(s)}
            </span>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto rounded border border-zinc-200">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="bg-zinc-50">
              <th className="w-16 border-r border-zinc-200 p-2 text-left text-zinc-500">Time</th>
              {days.map((d) => (
                <th key={d.toISOString()} className="border-r border-zinc-200 p-2 text-center">
                  {d.toLocaleDateString('en-CA', { weekday: 'short', month: 'short', day: 'numeric' })}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {hours.map((h) => (
              <tr key={h} className="border-t border-zinc-100">
                <td className="border-r border-zinc-200 p-2 text-zinc-400">{h}:00</td>
                {days.map((d) => {
                  const slotStart = `${formatDate(d)}T${String(h).padStart(2, '0')}:00:00`;
                  const appt = appointments.find(
                    (a) =>
                      a.start_time.startsWith(formatDate(d)) &&
                      new Date(a.start_time).getHours() === h,
                  );
                  return (
                    <td
                      key={d.toISOString()}
                      className="relative border-r border-zinc-100 p-1"
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        const id = e.dataTransfer.getData('appt-id');
                        const found = appointments.find((a) => a.id === id);
                        if (found) setPending({ appt: found, newStart: slotStart });
                      }}
                    >
                      {appt && (
                        <div
                          draggable
                          onDragStart={(e) => e.dataTransfer.setData('appt-id', appt.id)}
                          onClick={() => setDrawerApptId(appt.id)}
                          className={`cursor-pointer rounded px-1 py-0.5 ${apptStatusColor(appt.status)}`}
                          title={`${formatTime(appt.start_time)} – ${formatTime(appt.end_time)}`}
                        >
                          {formatTime(appt.start_time)} #{appt.patient_id.slice(0, 4)}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Appointment detail drawer */}
      <AppointmentDrawer
        appointmentId={drawerApptId}
        open={!!drawerApptId}
        onClose={() => setDrawerApptId(null)}
        onChanged={() => qc.invalidateQueries({ queryKey: ['appointments', clinicId] })}
      />

      {/* Drag-reschedule confirm dialog */}
      {pending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-80 rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-2 font-semibold">Confirm Reschedule</h3>
            <p className="mb-4 text-sm text-zinc-600">
              Move appointment to{' '}
              <strong>{new Date(pending.newStart).toLocaleString('en-CA')}</strong>?
            </p>
            <div className="flex justify-end gap-2">
              <button
                className="rounded px-3 py-1 text-sm hover:bg-zinc-100"
                onClick={() => setPending(null)}
              >
                Cancel
              </button>
              <button
                className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                onClick={confirmReschedule}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Conflict toast */}
      {conflictMsg && (
        <div className="fixed bottom-4 right-4 z-50 rounded bg-red-600 px-4 py-2 text-sm text-white shadow-lg">
          Conflict: {conflictMsg}
          <button className="ml-3 underline" onClick={() => setConflictMsg(null)}>
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
