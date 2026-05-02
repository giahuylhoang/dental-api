import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';

interface Props {
  leadId: string;
}

interface FormData {
  kind: string;
  body: string;
}

const KINDS = ['note', 'call', 'email', 'meeting'];

export default function AddActivityForm({ leadId }: Props) {
  const qc = useQueryClient();
  const { register, handleSubmit, reset } = useForm<FormData>({ defaultValues: { kind: 'note' } });

  const add = useMutation({
    mutationFn: (data: FormData) =>
      fetcher(`/api/v2/crm/leads/${leadId}/activities`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lead-activities', leadId] });
      reset({ kind: 'note' });
    },
  });

  return (
    <form onSubmit={handleSubmit((d) => add.mutate(d))} className="mb-4 flex flex-col gap-2 rounded border border-zinc-200 bg-zinc-50 p-3">
      <select {...register('kind')} aria-label="kind" className="rounded border border-zinc-300 px-2 py-1 text-sm">
        {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
      </select>
      <textarea {...register('body', { required: true })} aria-label="body" placeholder="Add a note…" rows={2} className="rounded border border-zinc-300 px-2 py-1 text-sm" />
      <button type="submit" disabled={add.isPending} className="self-end rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
        Add
      </button>
    </form>
  );
}
