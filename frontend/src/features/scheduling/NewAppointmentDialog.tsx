import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';

interface Props {
  open: boolean;
  onClose: () => void;
}

interface FormState {
  patient_id: string;
  doctor_id: string;
  operatory_id: string;
  service_id: string;
  start_time: string;
  duration_min: string;
  recurrence: 'none' | 'daily' | 'weekly' | 'monthly';
  recurrence_count: string;
}

export default function NewAppointmentDialog({ open, onClose }: Props) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [form, setForm] = useState<FormState>({
    patient_id: '',
    doctor_id: '',
    operatory_id: '',
    service_id: '',
    start_time: '',
    duration_min: '60',
    recurrence: 'none',
    recurrence_count: '1',
  });

  const create = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      fetcher('/api/v2/scheduling/appointments', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['appointments', clinicId] });
      onClose();
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const start = new Date(form.start_time);
    const end = new Date(start.getTime() + parseInt(form.duration_min) * 60000);
    create.mutate({
      patient_id: form.patient_id,
      doctor_id: parseInt(form.doctor_id),
      operatory_id: form.operatory_id || undefined,
      service_id: parseInt(form.service_id),
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      recurrence: form.recurrence !== 'none'
        ? { freq: form.recurrence, count: parseInt(form.recurrence_count) }
        : undefined,
    });
  }

  function set(k: keyof FormState, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-96 rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 font-semibold">New Appointment</h3>
        <form onSubmit={handleSubmit} className="space-y-3 text-sm">
          <div>
            <label className="block text-zinc-600">Patient ID</label>
            <input
              required
              className="mt-1 w-full rounded border px-2 py-1"
              value={form.patient_id}
              onChange={(e) => set('patient_id', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Provider ID</label>
            <input
              required
              className="mt-1 w-full rounded border px-2 py-1"
              value={form.doctor_id}
              onChange={(e) => set('doctor_id', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Operatory ID (optional)</label>
            <input
              className="mt-1 w-full rounded border px-2 py-1"
              value={form.operatory_id}
              onChange={(e) => set('operatory_id', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Service ID</label>
            <input
              required
              className="mt-1 w-full rounded border px-2 py-1"
              value={form.service_id}
              onChange={(e) => set('service_id', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Start Time</label>
            <input
              required
              type="datetime-local"
              className="mt-1 w-full rounded border px-2 py-1"
              value={form.start_time}
              onChange={(e) => set('start_time', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Duration (min)</label>
            <input
              type="number"
              min="15"
              className="mt-1 w-full rounded border px-2 py-1"
              value={form.duration_min}
              onChange={(e) => set('duration_min', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Recurrence</label>
            <select
              className="mt-1 w-full rounded border px-2 py-1"
              value={form.recurrence}
              onChange={(e) => set('recurrence', e.target.value as FormState['recurrence'])}
            >
              <option value="none">None</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          {form.recurrence !== 'none' && (
            <div>
              <label className="block text-zinc-600">Repeat count</label>
              <input
                type="number"
                min="1"
                className="mt-1 w-full rounded border px-2 py-1"
                value={form.recurrence_count}
                onChange={(e) => set('recurrence_count', e.target.value)}
              />
            </div>
          )}
          {create.error && (
            <p className="text-xs text-red-600">{(create.error as Error).message}</p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="rounded px-3 py-1 hover:bg-zinc-100" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              disabled={create.isPending}
              className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {create.isPending ? 'Saving…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
