import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import FormField from '../../components/forms/FormField';

const schema = z.object({
  medical_history: z.string(),
  allergies: z.string(),
  medications: z.string(),
  bisphosphonates_use: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const DEFAULTS: FormValues = { medical_history: '', allergies: '', medications: '', bisphosphonates_use: false };

interface MedicalFormProps {
  patientId: string;
}

export default function MedicalForm({ patientId }: MedicalFormProps) {
  const [toast, setToast] = useState('');

  const { data, isLoading } = useQuery<FormValues | null>({
    queryKey: ['medical-history', patientId],
    queryFn: () => fetcher<FormValues | null>(`/api/v2/clinical/patients/${patientId}/medical-history`),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: DEFAULTS,
  });

  useEffect(() => {
    if (data) reset(data);
  }, [data, reset]);

  const saveMutation = useMutation({
    mutationFn: (values: FormValues) =>
      fetcher<FormValues>(`/api/v2/clinical/patients/${patientId}/medical-history`, {
        method: 'POST',
        body: JSON.stringify(values),
      }),
    onSuccess: (saved) => {
      reset(saved);
      setToast('Saved successfully');
      setTimeout(() => setToast(''), 3000);
    },
    onError: (err: Error) => {
      setToast(err.message);
      setTimeout(() => setToast(''), 3000);
    },
  });

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  return (
    <form onSubmit={handleSubmit((v) => saveMutation.mutate(v))} className="space-y-4">
      {toast && (
        <div className="rounded bg-green-50 px-3 py-2 text-sm text-green-700">{toast}</div>
      )}
      <FormField label="Medical History" name="medical_history" error={errors.medical_history?.message}>
        <textarea
          id="medical_history"
          rows={4}
          {...register('medical_history')}
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </FormField>
      <FormField label="Allergies" name="allergies" error={errors.allergies?.message}>
        <textarea
          id="allergies"
          rows={3}
          {...register('allergies')}
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </FormField>
      <FormField label="Medications" name="medications" error={errors.medications?.message}>
        <textarea
          id="medications"
          rows={3}
          {...register('medications')}
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </FormField>
      <div className="flex items-center gap-2">
        <input
          id="bisphosphonates_use"
          type="checkbox"
          {...register('bisphosphonates_use')}
          className="h-4 w-4 rounded border-zinc-300"
        />
        <label htmlFor="bisphosphonates_use" className="text-sm text-zinc-700">
          Bisphosphonates use
        </label>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saveMutation.isPending}
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-50"
        >
          Save
        </button>
        <button
          type="button"
          onClick={() => reset(data ?? DEFAULTS)}
          disabled={!isDirty}
          className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50 disabled:opacity-40"
        >
          Reset
        </button>
      </div>
    </form>
  );
}
