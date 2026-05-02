import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import Drawer from '../../components/Drawer';
import FormField from '../../components/forms/FormField';
import type { components } from '../../api/v2/types';

type PatientInsurance = components['schemas']['PatientInsurance'];

const schema = z.object({
  carrier: z.string().min(1, 'Required'),
  policy_number: z.string().min(1, 'Required'),
  group_number: z.string().optional(),
  holder_name: z.string().min(1, 'Required'),
  holder_relationship: z.string().optional(),
  is_primary: z.boolean(),
  assignment_of_benefits: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

interface InsuranceDrawerProps {
  patientId: string;
  insurance?: PatientInsurance;
  open: boolean;
  onClose: () => void;
}

export default function InsuranceDrawer({ patientId, insurance, open, onClose }: InsuranceDrawerProps) {
  const qc = useQueryClient();
  const isEdit = !!insurance?.id;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      carrier: '',
      policy_number: '',
      group_number: '',
      holder_name: '',
      holder_relationship: '',
      is_primary: false,
      assignment_of_benefits: false,
    },
  });

  useEffect(() => {
    if (insurance) {
      reset({
        carrier: insurance.carrier,
        policy_number: insurance.policy_number,
        group_number: insurance.group_number ?? '',
        holder_name: insurance.holder_name,
        holder_relationship: insurance.holder_relationship ?? '',
        is_primary: insurance.is_primary,
        assignment_of_benefits: insurance.assignment_of_benefits,
      });
    } else {
      reset({ carrier: '', policy_number: '', group_number: '', holder_name: '', holder_relationship: '', is_primary: false, assignment_of_benefits: false });
    }
  }, [insurance, reset]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      if (isEdit) {
        return fetcher<PatientInsurance>(
          `/api/v2/clinical/patients/${patientId}/insurance/${insurance!.id}`,
          { method: 'PUT', body: JSON.stringify(values) },
        );
      }
      return fetcher<PatientInsurance>(
        `/api/v2/clinical/patients/${patientId}/insurance`,
        { method: 'POST', body: JSON.stringify(values) },
      );
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['insurance', patientId] });
      onClose();
    },
  });

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isEdit ? 'Edit Insurance' : 'Add Insurance'}
      footer={
        <div className="flex gap-2">
          <button
            form="insurance-form"
            type="submit"
            disabled={mutation.isPending}
            className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-50"
          >
            {isEdit ? 'Update' : 'Add'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
          >
            Cancel
          </button>
        </div>
      }
    >
      <form id="insurance-form" onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
        <FormField label="Carrier" name="carrier" required error={errors.carrier?.message}>
          <input
            id="carrier"
            {...register('carrier')}
            className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </FormField>
        <FormField label="Policy Number" name="policy_number" required error={errors.policy_number?.message}>
          <input
            id="policy_number"
            {...register('policy_number')}
            className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </FormField>
        <FormField label="Group Number" name="group_number" error={errors.group_number?.message}>
          <input
            id="group_number"
            {...register('group_number')}
            className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </FormField>
        <FormField label="Holder Name" name="holder_name" required error={errors.holder_name?.message}>
          <input
            id="holder_name"
            {...register('holder_name')}
            className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </FormField>
        <FormField label="Holder Relationship" name="holder_relationship" error={errors.holder_relationship?.message}>
          <input
            id="holder_relationship"
            {...register('holder_relationship')}
            className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </FormField>
        <div className="flex items-center gap-2">
          <input id="is_primary" type="checkbox" {...register('is_primary')} className="h-4 w-4 rounded border-zinc-300" />
          <label htmlFor="is_primary" className="text-sm text-zinc-700">Primary insurance</label>
        </div>
        <div className="flex items-center gap-2">
          <input id="assignment_of_benefits" type="checkbox" {...register('assignment_of_benefits')} className="h-4 w-4 rounded border-zinc-300" />
          <label htmlFor="assignment_of_benefits" className="text-sm text-zinc-700">Assignment of benefits</label>
        </div>
        {mutation.isError && (
          <p className="text-sm text-red-600">{(mutation.error as Error).message}</p>
        )}
      </form>
    </Drawer>
  );
}
