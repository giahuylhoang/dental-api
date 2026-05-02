import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import QuickBookPopover from '../patients/QuickBookPopover';

interface Patient {
  id: string;
  first_name: string;
  last_name: string;
}

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
  // Convert ISO string to datetime-local format (YYYY-MM-DDTHH:mm)
  return iso.slice(0, 16);
}

export default function NewAppointmentDialog({ open, start, end, onClose, onCreated }: Props) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();

  const [patientQuery, setPatientQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [showQuickBook, setShowQuickBook] = useState(false);
  const [doctorId, setDoctorId] = useState('');
  const [serviceId, setServiceId] = useState('');
  const [startVal, setStartVal] = useState(toDatetimeLocal(start));
  const [endVal, setEndVal] = useState(toDatetimeLocal(end));
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [notes, setNotes] = useState('');

  const { data: patientResults = [] } = useQuery<{ items: Patient[] }>({
    queryKey: ['patients-search', patientQuery, clinicId],
    queryFn: () => fetcher<{ items: Patient[] }>(`/api/patients?q=${encodeURIComponent(patientQuery)}&limit=10`),
    enabled: open && patientQuery.length > 0 && !selectedPatient,
    select: (d) => d,
  });

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

  if (!open) return null;

  const patientItems = (patientResults as unknown as { items?: Patient[] })?.items ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-[28rem] rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 font-semibold">New Appointment</h3>
        <form onSubmit={handleSubmit} className="space-y-3 text-sm">
          {/* Patient combobox */}
          <div>
            <label className="block text-zinc-600">Patient</label>
            {selectedPatient ? (
              <div className="mt-1 flex items-center gap-2">
                <span className="flex-1 rounded border px-2 py-1 bg-zinc-50">
                  {selectedPatient.first_name} {selectedPatient.last_name}
                </span>
                <button
                  type="button"
                  className="text-xs text-zinc-500 hover:text-zinc-800"
                  onClick={() => setSelectedPatient(null)}
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="relative mt-1">
                <input
                  className="w-full rounded border px-2 py-1"
                  placeholder="Search patient…"
                  value={patientQuery}
                  onChange={(e) => setPatientQuery(e.target.value)}
                  aria-label="Search patient"
                />
                {patientItems.length > 0 && (
                  <ul className="absolute z-10 mt-1 w-full rounded border bg-white shadow-md">
                    {patientItems.map((p) => (
                      <li
                        key={p.id}
                        className="cursor-pointer px-3 py-1.5 hover:bg-zinc-100"
                        onClick={() => {
                          setSelectedPatient(p);
                          setPatientQuery('');
                        }}
                      >
                        {p.first_name} {p.last_name}
                      </li>
                    ))}
                  </ul>
                )}
                {patientQuery.length > 0 && patientItems.length === 0 && (
                  <div className="mt-1">
                    <button
                      type="button"
                      className="text-xs text-blue-600 hover:underline"
                      onClick={() => setShowQuickBook(true)}
                    >
                      + Create new patient
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Provider */}
          <div>
            <label className="block text-zinc-600">Provider</label>
            <select
              required
              className="mt-1 w-full rounded border px-2 py-1"
              value={doctorId}
              onChange={(e) => setDoctorId(e.target.value)}
            >
              <option value="">Select provider…</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          {/* Service */}
          <div>
            <label className="block text-zinc-600">Service</label>
            <select
              required
              className="mt-1 w-full rounded border px-2 py-1"
              value={serviceId}
              onChange={(e) => setServiceId(e.target.value)}
            >
              <option value="">Select service…</option>
              {services.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          {/* Start */}
          <div>
            <label className="block text-zinc-600">Start</label>
            <input
              required
              type="datetime-local"
              className="mt-1 w-full rounded border px-2 py-1"
              value={startVal}
              onChange={(e) => setStartVal(e.target.value)}
            />
          </div>

          {/* End */}
          <div>
            <label className="block text-zinc-600">End</label>
            <input
              required
              type="datetime-local"
              className="mt-1 w-full rounded border px-2 py-1"
              value={endVal}
              onChange={(e) => setEndVal(e.target.value)}
            />
          </div>

          {/* Chief complaint */}
          <div>
            <label className="block text-zinc-600">Pain points / Chief complaint</label>
            <textarea
              className="mt-1 w-full rounded border px-2 py-1"
              rows={2}
              value={chiefComplaint}
              onChange={(e) => setChiefComplaint(e.target.value)}
              aria-label="Pain points / Chief complaint"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-zinc-600">Notes</label>
            <textarea
              className="mt-1 w-full rounded border px-2 py-1"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          {create.error && (
            <p className="text-xs text-red-600">{(create.error as Error).message}</p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="rounded px-3 py-1 hover:bg-zinc-100" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              disabled={create.isPending || !selectedPatient}
              className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {create.isPending ? 'Saving…' : 'Create'}
            </button>
          </div>
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
      </div>
    </div>
  );
}
