import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import DateTimePicker from './DateTimePicker';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import {
  type ApptStatus,
  nextAllowed,
  statusColor,
  statusLabel,
} from './appt-status';
import { PatientChip } from '../patients/PatientChip';

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
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <SheetContent side="right" className="w-[400px] sm:max-w-[400px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Appointment Details</SheetTitle>
        </SheetHeader>

        {isLoading && <p className="text-sm text-zinc-500 mt-4">Loading…</p>}
        {appt && (
          <div className="space-y-4 text-sm mt-4">
            <div className="space-y-1">
              <div>
                <span className="text-zinc-500">Patient: </span>
                <PatientChip patientId={appt.patient_id} variant="card" linkTo="/patients/:id" />
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
                <Badge className={statusColor(currentStatus)} variant="outline">
                  {statusLabel(currentStatus)}
                </Badge>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-zinc-100 pt-3">
              <Button
                size="sm"
                variant="default"
                disabled={!canDo('CONFIRMED')}
                onClick={() => updateStatus.mutate('CONFIRMED')}
              >
                Confirm
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!canDo('CHECKED_IN')}
                onClick={() => updateStatus.mutate('CHECKED_IN')}
              >
                Check in
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!canDo('IN_PROGRESS')}
                onClick={() => updateStatus.mutate('IN_PROGRESS')}
              >
                Start
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!canDo('COMPLETED')}
                onClick={() => updateStatus.mutate('COMPLETED')}
              >
                Complete
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!canDo('NO_SHOW')}
                onClick={() => updateStatus.mutate('NO_SHOW')}
              >
                No show
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => setShowCancel(true)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowReschedule((v) => !v)}
              >
                Reschedule
              </Button>
            </div>

            {showReschedule && (
              <div className="flex items-center gap-2 border-t border-zinc-100 pt-3">
                <DateTimePicker value={newStart} onChange={setNewStart} />
                <Button
                  size="sm"
                  disabled={!newStart || rescheduleMut.isPending}
                  onClick={handleReschedule}
                >
                  Save
                </Button>
              </div>
            )}

            {updateStatus.error && (
              <p className="text-xs text-red-600">{(updateStatus.error as Error).message}</p>
            )}
          </div>
        )}

        {/* Cancel confirmation */}
        {showCancel && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
            <div className="w-72 rounded-lg bg-white p-5 shadow-xl">
              <p className="mb-4 text-sm">Cancel this appointment?</p>
              <div className="flex justify-end gap-2">
                <Button variant="ghost" size="sm" onClick={() => setShowCancel(false)}>
                  No
                </Button>
                <Button variant="destructive" size="sm" onClick={() => cancelMut.mutate()}>
                  Yes, cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
