import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import QuickBookPopover from '../patients/QuickBookPopover';
import { PatientSearchInput } from '../patients/PatientSearchInput';
import type { Patient } from '../patients/usePatient';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';

interface Doctor {
  id: number;
  name: string;
}

interface Service {
  id: number;
  name: string;
}

interface Props {
  open: boolean;
  start: string;
  end: string;
  onClose: () => void;
  onCreated: () => void;
}

function toDatetimeLocal(iso: string): string {
  if (!iso) return '';
  return iso.slice(0, 16);
}

export default function NewAppointmentDialog({ open, start, end, onClose, onCreated }: Props) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [showQuickBook, setShowQuickBook] = useState(false);
  const [doctorId, setDoctorId] = useState('');
  const [serviceId, setServiceId] = useState('');
  const [startVal, setStartVal] = useState(toDatetimeLocal(start));
  const [endVal, setEndVal] = useState(toDatetimeLocal(end));
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [notes, setNotes] = useState('');

  const { data: doctors = [] } = useQuery<Doctor[]>({
    queryKey: ['doctors', clinicId],
    queryFn: () => fetcher<Doctor[]>('/api/doctors'),
    enabled: open,
  });

  const { data: services = [] } = useQuery<Service[]>({
    queryKey: ['services', clinicId],
    queryFn: () => fetcher<Service[]>('/api/services'),
    enabled: open,
  });

  const create = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      fetcher('/api/calendar/events', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calendar-events', clinicId] });
      onCreated();
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPatient) return;
    create.mutate({
      patient_id: selectedPatient.id,
      doctor_id: parseInt(doctorId),
      service_id: parseInt(serviceId),
      start_time: new Date(startVal).toISOString(),
      end_time: new Date(endVal).toISOString(),
      chief_complaint: chiefComplaint || undefined,
      notes: notes || undefined,
    });
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="sm:max-w-[28rem]">
        <DialogHeader>
          <DialogTitle>New Appointment</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3 text-sm">
          {/* Patient */}
          <div>
            <label className="block text-zinc-600 mb-1">Patient</label>
            {selectedPatient ? (
              <div className="flex items-center gap-2">
                <span className="flex-1 rounded border px-2 py-1 bg-zinc-50 text-sm">
                  {selectedPatient.first_name} {selectedPatient.last_name}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedPatient(null)}
                >
                  ✕
                </Button>
              </div>
            ) : (
              <div>
                <PatientSearchInput
                  onSelect={(p) => setSelectedPatient(p)}
                  placeholder="Search patient…"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="mt-1 text-xs text-blue-600 hover:underline p-0 h-auto"
                  onClick={() => setShowQuickBook(true)}
                >
                  + Create new patient
                </Button>
              </div>
            )}
          </div>

          {/* Provider */}
          <div>
            <label className="block text-zinc-600 mb-1">Provider</label>
            <Select required value={doctorId} onValueChange={setDoctorId}>
              <SelectTrigger data-testid="provider-select">
                <SelectValue placeholder="Select provider…" />
              </SelectTrigger>
              <SelectContent>
                {doctors.map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Service */}
          <div>
            <label className="block text-zinc-600 mb-1">Service</label>
            <Select required value={serviceId} onValueChange={setServiceId}>
              <SelectTrigger data-testid="service-select">
                <SelectValue placeholder="Select service…" />
              </SelectTrigger>
              <SelectContent>
                {services.map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Start */}
          <div>
            <label className="block text-zinc-600 mb-1">Start</label>
            <Input
              required
              type="datetime-local"
              value={startVal}
              onChange={(e) => setStartVal(e.target.value)}
            />
          </div>

          {/* End */}
          <div>
            <label className="block text-zinc-600 mb-1">End</label>
            <Input
              required
              type="datetime-local"
              value={endVal}
              onChange={(e) => setEndVal(e.target.value)}
            />
          </div>

          {/* Chief complaint */}
          <div>
            <label className="block text-zinc-600 mb-1" htmlFor="chief-complaint">
              Pain points / Chief complaint
            </label>
            <Textarea
              id="chief-complaint"
              rows={2}
              value={chiefComplaint}
              onChange={(e) => setChiefComplaint(e.target.value)}
              aria-label="Pain points / Chief complaint"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-zinc-600 mb-1">Notes</label>
            <Textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          {create.error && (
            <p className="text-xs text-red-600">{(create.error as Error).message}</p>
          )}

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={create.isPending || !selectedPatient}>
              {create.isPending ? 'Saving…' : 'Create'}
            </Button>
          </DialogFooter>
        </form>

        {showQuickBook && (
          <QuickBookPopover
            onCreated={(patient) => {
              setSelectedPatient(patient);
              setShowQuickBook(false);
            }}
            onClose={() => setShowQuickBook(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
