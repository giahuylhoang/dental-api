import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';

interface FormData {
  working_hour_start: string;
  working_hour_end: string;
}

interface Props {
  defaultValues: FormData;
}

export default function WorkingHoursCard({ defaultValues }: Props) {
  const [open, setOpen] = useState(false);
  const [saved, setSaved] = useState(false);
  const qc = useQueryClient();

  const { register, handleSubmit } = useForm<FormData>({ defaultValues });

  const save = useMutation({
    mutationFn: (data: FormData) =>
      fetcher('/api/v2/settings/clinic', { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings', 'clinic'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  return (
    <div className="rounded-lg border border-zinc-200">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left font-semibold"
        onClick={() => setOpen((o) => !o)}
      >
        Working Hours
        <span>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <form onSubmit={handleSubmit((d) => save.mutate(d))} className="flex flex-col gap-3 px-4 pb-4">
          <input
            {...register('working_hour_start')}
            aria-label="working_hour_start"
            type="time"
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
          />
          <input
            {...register('working_hour_end')}
            aria-label="working_hour_end"
            type="time"
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
          />
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={save.isPending}
              className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Save
            </button>
            {saved && <span className="text-green-600">Saved</span>}
          </div>
        </form>
      )}
    </div>
  );
}
