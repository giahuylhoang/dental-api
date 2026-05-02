import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import InsuranceDrawer from './InsuranceDrawer';
import type { components } from '../../api/v2/types';

type PatientInsurance = components['schemas']['PatientInsurance'];

interface InsuranceListProps {
  patientId: string;
}

export default function InsuranceList({ patientId }: InsuranceListProps) {
  const qc = useQueryClient();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<PatientInsurance | undefined>(undefined);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: insurances = [], isLoading } = useQuery<PatientInsurance[]>({
    queryKey: ['insurance', patientId],
    queryFn: () => fetcher<PatientInsurance[]>(`/api/v2/clinical/patients/${patientId}/insurance`),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      fetcher<void>(`/api/v2/clinical/patients/${patientId}/insurance/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['insurance', patientId] });
      setDeletingId(null);
    },
  });

  function openAdd() {
    setEditing(undefined);
    setDrawerOpen(true);
  }

  function openEdit(ins: PatientInsurance) {
    setEditing(ins);
    setDrawerOpen(true);
  }

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <button
          onClick={openAdd}
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700"
        >
          Add insurance
        </button>
      </div>

      {insurances.length === 0 && (
        <p className="text-sm text-zinc-500">No insurance records.</p>
      )}

      {insurances.map((ins) => (
        <div
          key={ins.id}
          className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2 text-sm hover:bg-zinc-50 cursor-pointer"
          onClick={() => openEdit(ins)}
        >
          <div className="space-y-0.5">
            <div className="font-medium">{ins.carrier}</div>
            <div className="text-zinc-500">
              Policy: {ins.policy_number}
              {ins.group_number ? ` · Group: ${ins.group_number}` : ''}
            </div>
            <div className="text-zinc-500">Holder: {ins.holder_name}</div>
          </div>
          <div className="flex items-center gap-2">
            {ins.is_primary && (
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">Primary</span>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); setDeletingId(ins.id ?? null); }}
              className="rounded border border-zinc-200 px-2 py-1 text-xs text-zinc-600 hover:bg-red-50 hover:text-red-600"
            >
              Delete
            </button>
          </div>
        </div>
      ))}

      {deletingId && (
        <div className="rounded border border-zinc-200 bg-zinc-50 p-4">
          <p className="mb-3 text-sm">Delete this insurance record?</p>
          <div className="flex gap-2">
            <button
              onClick={() => deleteMutation.mutate(deletingId)}
              disabled={deleteMutation.isPending}
              className="rounded bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700 disabled:opacity-50"
            >
              Delete
            </button>
            <button
              onClick={() => setDeletingId(null)}
              className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <InsuranceDrawer
        patientId={patientId}
        insurance={editing}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
