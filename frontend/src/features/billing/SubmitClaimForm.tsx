import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import FormField from '../../components/forms/FormField';

interface PatientInsurance {
  id: string;
  carrier: string;
}

interface Props {
  invoiceId: string;
  patientId: string;
  onSuccess: (claimId: string) => void;
  onCancel: () => void;
}

export default function SubmitClaimForm({ invoiceId, patientId, onSuccess, onCancel }: Props) {
  const [carrier, setCarrier] = useState('');
  const [kind, setKind] = useState<'claim' | 'predetermination'>('claim');

  const { data: insurances = [] } = useQuery<PatientInsurance[]>({
    queryKey: ['insurance', patientId],
    queryFn: () => fetcher<PatientInsurance[]>(`/api/v2/clinical/patients/${patientId}/insurance`),
  });

  const submit = useMutation({
    mutationFn: () =>
      fetcher<{ id: string }>('/api/v2/insurance/claims', {
        method: 'POST',
        body: JSON.stringify({ invoice_id: invoiceId, carrier, kind }),
      }),
    onSuccess: (data) => onSuccess(data.id),
  });

  return (
    <div className="space-y-3 rounded border border-zinc-200 p-3">
      <h4 className="text-sm font-semibold">Submit Insurance Claim</h4>
      <FormField label="Carrier" name="carrier">
        <select
          id="carrier"
          className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
          value={carrier}
          onChange={(e) => setCarrier(e.target.value)}
        >
          <option value="">Select carrier…</option>
          {insurances.map((ins) => (
            <option key={ins.id} value={ins.carrier}>
              {ins.carrier}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Kind" name="kind">
        <select
          id="kind"
          className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
          value={kind}
          onChange={(e) => setKind(e.target.value as typeof kind)}
        >
          <option value="claim">Claim</option>
          <option value="predetermination">Predetermination</option>
        </select>
      </FormField>
      {submit.error && (
        <p className="text-xs text-red-600">{(submit.error as Error).message}</p>
      )}
      <div className="flex gap-2">
        <button
          disabled={submit.isPending || !carrier}
          onClick={() => submit.mutate()}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submit.isPending ? 'Submitting…' : 'Submit Claim'}
        </button>
        <button
          onClick={onCancel}
          className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
