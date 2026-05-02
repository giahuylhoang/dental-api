import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import Drawer from '../../components/Drawer';
import DateTimePicker from './DateTimePicker';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import {
  type ApptStatus,
  nextAllowed,
  statusColor,
  statusLabel,
} from './appt-status';

interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: number;
  service_id: number;
  start_time: string;
  end_time: string;
  status: string;
  notes?: string;
  patient_name?: string;
  doctor_name?: string;
  service_name?: string;
}

interface Props {
  appointmentId: string | null;
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
}

function normalizeStatus(s: string): ApptStatus {
  return s.toUpperCase() as ApptStatus;
}

export default function AppointmentDrawer({ appointmentId, open, onClose, onChanged }: Props) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [showCancel, setShowCancel] = useState(false);
  const [showReschedule, setShowReschedule] = useState(false);
  const [newStart, setNewStart] = useState<Date | null>(null);

  const { data: appt, isLoading } = useQuery<Appointment>({
    queryKey: ['appointment', appointmentId, clinicId],
    queryFn: () => fetcher<Appointment>(`/api/appointments/${appointmentId}`),
    enabled: open && !!appointmentId,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['appointment', appointmentId] });
    qc.invalidateQueries({ queryKey: ['appointments'] });
    onChanged();
  };

  const updateStatus = useMutation({
    mutationFn: (status: string) =>
      fetcher(`/api/appointments/${appointmentId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status }),
      }),
    onSuccess: invalidate,
  });

  const cancelMut = useMutation({
    mutationFn: () =>
      fetcher(`/api/appointments/${appointmentId}/cancel`, { method: 'PUT' }),
    onSuccess: () => {
      setShowCancel(false);
      invalidate();
    },
  });

  const rescheduleMut = useMutation({
    mutationFn: ({ start_time, end_time }: { start_time: string; end_time: string }) =>
      fetcher(`/api/appointments/${appointmentId}/reschedule`, {
        method: 'PUT',
        body: JSON.stringify({ start_time, end_time }),
      }),
    onSuccess: () => {
      setShowReschedule(false);
      setNewStart(null);
      invalidate();
    },
  });

  function handleReschedule() {
    if (!newStart || !appt) return;
    const duration = new Date(appt.end_time).getTime() - new Date(appt.start_time).getTime();
    rescheduleMut.mutate({
      start_time: newStart.toISOString(),
      end_time: new Date(newStart.getTime() + duration).toISOString(),
    });
  }

  const currentStatus = appt ? normalizeStatus(appt.status) : 'SCHEDULED';
  const allowed = nextAllowed(currentStatus);

  const canDo = (s: ApptStatus) => allowed.includes(s);

  return (
    <Drawer open={open} onClose={onClose} title="Appointment Details" width="md">
      {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}
      {appt && (
        <div className="space-y-4 text-sm">
          <div className="space-y-1">
            <div>
              <span className="text-zinc-500">Patient: </span>
              <Link
                to={`/patients/${appt.patient_id}`}
                className="text-blue-600 hover:underline"
              >
                {appt.patient_name ?? appt.patient_id}
              </Link>
            </div>
            <div>
              <span className="text-zinc-500">Provider: </span>
              {appt.doctor_name ?? `Doctor #${appt.doctor_id}`}
            </div>
            <div>
              <span className="text-zinc-500">Service: </span>
              {appt.service_name ?? `Service #${appt.service_id}`}
            </div>
            <div>
              <span className="text-zinc-500">Time: </span>
              {new Date(appt.start_time).toLocaleString()} – {new Date(appt.end_time).toLocaleTimeString()}
            </div>
            {appt.notes && (
              <div>
                <span className="text-zinc-500">Notes: </span>
                {appt.notes}
              </div>
            )}
            <div className="flex items-center gap-2">
              <span className="text-zinc-500">Status: </span>
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${statusColor(currentStatus)}`}>
                {statusLabel(currentStatus)}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 border-t border-zinc-100 pt-3">
            <button
              disabled={!canDo('CONFIRMED')}
              onClick={() => updateStatus.mutate('CONFIRMED')}
              className="rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700 disabled:opacity-40"
            >
              Confirm
            </button>
            <button
              disabled={!canDo('CHECKED_IN')}
              onClick={() => updateStatus.mutate('CHECKED_IN')}
              className="rounded bg-yellow-500 px-3 py-1 text-xs text-white hover:bg-yellow-600 disabled:opacity-40"
            >
              Check in
            </button>
            <button
              disabled={!canDo('IN_PROGRESS')}
              onClick={() => updateStatus.mutate('IN_PROGRESS')}
              className="rounded bg-orange-500 px-3 py-1 text-xs text-white hover:bg-orange-600 disabled:opacity-40"
            >
              Start
            </button>
            <button
              disabled={!canDo('COMPLETED')}
              onClick={() => updateStatus.mutate('COMPLETED')}
              className="rounded bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-40"
            >
              Complete
            </button>
            <button
              disabled={!canDo('NO_SHOW')}
              onClick={() => updateStatus.mutate('NO_SHOW')}
              className="rounded bg-red-500 px-3 py-1 text-xs text-white hover:bg-red-600 disabled:opacity-40"
            >
              No show
            </button>
            <button
              onClick={() => setShowCancel(true)}
              className="rounded border border-red-300 px-3 py-1 text-xs text-red-600 hover:bg-red-50"
            >
              Cancel
            </button>
            <button
              onClick={() => setShowReschedule((v) => !v)}
              className="rounded border border-zinc-300 px-3 py-1 text-xs hover:bg-zinc-50"
            >
              Reschedule
            </button>
          </div>

          {showReschedule && (
            <div className="flex items-center gap-2 border-t border-zinc-100 pt-3">
              <DateTimePicker value={newStart} onChange={setNewStart} />
              <button
                disabled={!newStart || rescheduleMut.isPending}
                onClick={handleReschedule}
                className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-40"
              >
                Save
              </button>
            </div>
          )}

          {updateStatus.error && (
            <p className="text-xs text-red-600">{(updateStatus.error as Error).message}</p>
          )}
        </div>
      )}

      {/* Cancel confirmation dialog */}
      {showCancel && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
          <div className="w-72 rounded-lg bg-white p-5 shadow-xl">
            <p className="mb-4 text-sm">Cancel this appointment?</p>
            <div className="flex justify-end gap-2">
              <button
                className="rounded px-3 py-1 text-sm hover:bg-zinc-100"
                onClick={() => setShowCancel(false)}
              >
                No
              </button>
              <button
                className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700"
                onClick={() => cancelMut.mutate()}
              >
                Yes, cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </Drawer>
  );
}
