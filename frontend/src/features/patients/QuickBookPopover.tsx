import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { fetcher } from '../../api/client';

interface Patient {
  id: string;
  first_name: string;
  last_name: string;
}

interface Props {
  onCreated: (patient: Patient) => void;
  onClose: () => void;
}

export default function QuickBookPopover({ onCreated, onClose }: Props) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');

  const create = useMutation({
    mutationFn: (body: { name: string; phone: string }) =>
      fetcher<Patient>('/api/v2/clinical/patients/quick-book', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (patient) => onCreated(patient),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate({ name, phone });
  }

  return (
    <div className="absolute inset-x-0 top-full z-20 mt-1 rounded-lg border bg-white p-4 shadow-xl">
      <h4 className="mb-3 text-sm font-semibold">Create new patient</h4>
      <form onSubmit={handleSubmit} className="space-y-2 text-sm">
        <div>
          <label className="block text-zinc-600">Full name</label>
          <input
            required
            className="mt-1 w-full rounded border px-2 py-1"
            value={name}
            onChange={(e) => setName(e.target.value)}
            aria-label="Full name"
          />
        </div>
        <div>
          <label className="block text-zinc-600">Phone</label>
          <input
            required
            className="mt-1 w-full rounded border px-2 py-1"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            aria-label="Phone"
          />
        </div>
        {create.error && (
          <p className="text-xs text-red-600">{(create.error as Error).message}</p>
        )}
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" className="rounded px-3 py-1 hover:bg-zinc-100" onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            disabled={create.isPending}
            className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {create.isPending ? 'Creating…' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  );
}
