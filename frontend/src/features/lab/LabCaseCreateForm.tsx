import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';

interface TreatmentPlan {
  id: string;
  status: string;
  patient_id: string;
}

interface Props {
  patientId?: string;
  onCreated?: (caseId: string) => void;
}

export default function LabCaseCreateForm({ patientId, onCreated }: Props) {
  const [vendorId, setVendorId] = useState('');
  const [dentureCaseId, setDentureCaseId] = useState('');
  const [labFee, setLabFee] = useState('');
  const [planId, setPlanId] = useState('');
  const [planQuery, setPlanQuery] = useState('');

  const { data: plans = [] } = useQuery<TreatmentPlan[]>({
    queryKey: ['treatment-plans-typeahead', patientId],
    queryFn: () =>
      fetcher<TreatmentPlan[]>(
        `/api/v2/treatment-plans${patientId ? `?patient_id=${patientId}` : ''}`,
      ),
    enabled: true,
  });

  const filteredPlans = planQuery
    ? plans.filter((p) => p.id.includes(planQuery) || p.status.includes(planQuery))
    : plans;

  const createMut = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      fetcher('/api/v2/lab/cases', { method: 'POST', body: JSON.stringify(body) }),
    onSuccess: (data: { id: string }) => onCreated?.(data.id),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createMut.mutate({
      vendor_id: vendorId,
      denture_case_id: dentureCaseId,
      lab_fee: labFee ? Number(labFee) : null,
      treatment_plan_id: planId || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 text-sm">
      <div>
        <label className="mb-1 block text-xs text-zinc-500">Vendor ID</label>
        <input
          value={vendorId}
          onChange={(e) => setVendorId(e.target.value)}
          placeholder="Vendor ID"
          className="w-full rounded border border-zinc-300 px-2 py-1 text-sm"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs text-zinc-500">Denture Case ID</label>
        <input
          value={dentureCaseId}
          onChange={(e) => setDentureCaseId(e.target.value)}
          placeholder="Denture Case ID"
          className="w-full rounded border border-zinc-300 px-2 py-1 text-sm"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs text-zinc-500">Lab Fee</label>
        <input
          type="number"
          value={labFee}
          onChange={(e) => setLabFee(e.target.value)}
          placeholder="0.00"
          className="w-full rounded border border-zinc-300 px-2 py-1 text-sm"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs text-zinc-500">Treatment Plan</label>
        <input
          value={planQuery}
          onChange={(e) => { setPlanQuery(e.target.value); setPlanId(''); }}
          placeholder="Search treatment plans…"
          className="w-full rounded border border-zinc-300 px-2 py-1 text-sm"
          aria-label="Search treatment plans"
        />
        {filteredPlans.length > 0 && !planId && (
          <ul className="mt-1 rounded border border-zinc-200 bg-white shadow-sm">
            {filteredPlans.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => { setPlanId(p.id); setPlanQuery(`${p.id} (${p.status})`); }}
                  className="w-full px-2 py-1 text-left text-xs hover:bg-zinc-50"
                >
                  {p.id} — {p.status}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <button
        type="submit"
        disabled={createMut.isPending}
        className="rounded bg-zinc-900 px-3 py-1.5 text-xs text-white disabled:opacity-40"
      >
        Create Case
      </button>
    </form>
  );
}
