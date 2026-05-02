import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import TreatmentPlanEditor from './TreatmentPlanEditor';
import { PatientSearchInput } from '../patients/PatientSearchInput';
import type { Patient } from '../patients/usePatient';

interface TreatmentPlan {
  id: string;
  patient_id: string;
  patient_name?: string;
  status: string;
  total_estimate: number;
  created_at?: string;
}

const STATUSES = ['draft', 'presented', 'accepted', 'in_progress', 'completed', 'declined'] as const;

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-zinc-100 text-zinc-600',
  presented: 'bg-blue-100 text-blue-700',
  accepted: 'bg-green-100 text-green-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-emerald-100 text-emerald-700',
  declined: 'bg-red-100 text-red-700',
};

export default function TreatmentPlansPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [showNewPlan, setShowNewPlan] = useState(false);
  const [chosenPatient, setChosenPatient] = useState<Patient | null>(null);

  const { data: plans = [] } = useQuery<TreatmentPlan[]>({
    queryKey: ['treatment-plans-all'],
    queryFn: () => fetcher<TreatmentPlan[]>('/api/v2/treatment-plans'),
  });

  const createPlanMutation = useMutation({
    mutationFn: (patientId: string) =>
      fetcher<TreatmentPlan>(`/api/v2/treatment-plans`, {
        method: 'POST',
        body: JSON.stringify({ patient_id: patientId, items: [] }),
      }),
    onSuccess: (plan) => {
      qc.invalidateQueries({ queryKey: ['treatment-plans-all'] });
      setShowNewPlan(false);
      setChosenPatient(null);
      setSelectedPlanId(plan.id);
      setSelectedPatientId(plan.patient_id);
    },
  });

  const filtered = plans.filter((p) => {
    if (statusFilter && p.status !== statusFilter) return false;
    if (search) {
      const name = p.patient_name?.toLowerCase() ?? '';
      if (!name.includes(search.toLowerCase())) return false;
    }
    return true;
  });

  if (selectedPlanId && selectedPatientId) {
    return (
      <div className="p-6">
        <button
          onClick={() => { setSelectedPlanId(null); setSelectedPatientId(null); }}
          className="mb-4 text-sm text-zinc-500 hover:text-zinc-800"
        >
          ← Back to plans
        </button>
        <TreatmentPlanEditor
          patientId={selectedPatientId}
          planId={selectedPlanId}
          onSaved={() => qc.invalidateQueries({ queryKey: ['treatment-plans-all'] })}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Treatment Plans</h2>
        <button
          onClick={() => setShowNewPlan(true)}
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700"
        >
          New plan
        </button>
      </div>

      {/* New plan dialog */}
      {showNewPlan && (
        <div className="rounded-lg border border-zinc-200 bg-white p-4 shadow-md space-y-3 max-w-sm">
          <h3 className="font-medium">New Treatment Plan</h3>
          <div className="relative">
            <PatientSearchInput
              onSelect={(p) => setChosenPatient(p)}
              placeholder="Search patient…"
            />
          </div>
          <div className="flex gap-2">
            <button
              disabled={!chosenPatient}
              onClick={() => chosenPatient && createPlanMutation.mutate(chosenPatient.id)}
              className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-40"
            >
              Create
            </button>
            <button
              onClick={() => { setShowNewPlan(false); setChosenPatient(null); }}
              className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Search */}
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by patient name…"
        className="w-full max-w-sm rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none"
      />

      {/* Status filter chips */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setStatusFilter(null)}
          className={`rounded-full px-3 py-1 text-xs ${statusFilter === null ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'}`}
        >
          All
        </button>
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s === statusFilter ? null : s)}
            className={`rounded-full px-3 py-1 text-xs ${statusFilter === s ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'}`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Plans table */}
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-200 text-left text-zinc-500">
            <th className="pb-2 pr-4 font-medium">Patient</th>
            <th className="pb-2 pr-4 font-medium">Status</th>
            <th className="pb-2 font-medium">Total estimate</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((plan) => (
            <tr
              key={plan.id}
              onClick={() => { setSelectedPlanId(plan.id); setSelectedPatientId(plan.patient_id); }}
              className="cursor-pointer border-b border-zinc-100 hover:bg-zinc-50"
            >
              <td className="py-2 pr-4">{plan.patient_name ?? plan.patient_id}</td>
              <td className="py-2 pr-4">
                <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_COLORS[plan.status] ?? 'bg-zinc-100 text-zinc-600'}`}>{plan.status}</span>
              </td>
              <td className="py-2">${plan.total_estimate.toFixed(2)}</td>
            </tr>
          ))}
          {filtered.length === 0 && (
            <tr>
              <td colSpan={3} className="py-4 text-center text-zinc-400">No plans found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
