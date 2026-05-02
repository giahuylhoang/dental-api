import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';

interface Props {
  open: boolean;
  onClose: () => void;
}

interface FormData {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  source: string;
  notes: string;
}

const SOURCES = ['phone', 'web', 'referral', 'walk-in', 'other'];

export default function LeadCreateDialog({ open, onClose }: Props) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const { register, handleSubmit, reset } = useForm<FormData>();

  const create = useMutation({
    mutationFn: (data: FormData) =>
      fetcher('/api/v2/crm/leads', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['leads', clinicId] });
      reset();
      onClose();
    },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div role="dialog" aria-modal="true" aria-label="New Lead" className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-base font-semibold">New Lead</h2>
        <form onSubmit={handleSubmit((d) => create.mutate(d))} className="flex flex-col gap-3">
          <input {...register('first_name', { required: true })} placeholder="First name" aria-label="first_name" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
          <input {...register('last_name', { required: true })} placeholder="Last name" aria-label="last_name" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
          <input {...register('phone')} placeholder="Phone" aria-label="phone" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
          <input {...register('email')} placeholder="Email" aria-label="email" type="email" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
          <select {...register('source')} aria-label="source" className="rounded border border-zinc-300 px-3 py-1.5 text-sm">
            <option value="">Source…</option>
            {SOURCES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <textarea {...register('notes')} placeholder="Notes" aria-label="notes" rows={3} className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-100">Cancel</button>
            <button type="submit" disabled={create.isPending} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
}
