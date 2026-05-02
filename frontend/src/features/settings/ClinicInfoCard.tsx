import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { zodV4Resolver } from '../../lib/zodResolver';

const TIMEZONES = [
  'America/Edmonton',
  'America/Toronto',
  'America/Vancouver',
  'America/New_York',
  'Europe/London',
  'UTC',
];

const schema = z.object({
  display_name: z.string().min(1, 'Name is required'),
  address: z.string(),
  contact_phone: z.string(),
  timezone: z.string(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  defaultValues: FormData;
}

export default function ClinicInfoCard({ defaultValues }: Props) {
  const [open, setOpen] = useState(true);
  const [saved, setSaved] = useState(false);
  const qc = useQueryClient();

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodV4Resolver(schema),
    defaultValues,
  });

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
        Clinic Info
        <span>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <form onSubmit={handleSubmit((d) => save.mutate(d))} className="flex flex-col gap-3 px-4 pb-4">
          <div>
            <input
              {...register('display_name')}
              aria-label="display_name"
              placeholder="Display name"
              className="w-full rounded border border-zinc-300 px-3 py-1.5 text-sm"
            />
            {errors.display_name && (
              <p role="alert" className="mt-1 text-xs text-red-600">{errors.display_name.message}</p>
            )}
          </div>
          <input
            {...register('address')}
            aria-label="address"
            placeholder="Address"
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
          />
          <input
            {...register('contact_phone')}
            aria-label="contact_phone"
            placeholder="Phone"
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
          />
          <select
            {...register('timezone')}
            aria-label="timezone"
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
          >
            {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
          </select>
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
