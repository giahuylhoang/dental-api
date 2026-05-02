import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Drawer from '../../components/Drawer';
import { fetcher } from '../../api/client';

interface DentureCase {
  id: string;
  patient_id: string;
  arch: string;
  case_type: string;
  current_stage: string;
  status: string;
  opened_at: string;
  closed_at: string | null;
  notes: string | null;
}

interface Props {
  caseId: string | null;
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
}

export default function DentureCaseDrawer({ caseId, open, onClose, onChanged }: Props) {
  const qc = useQueryClient();

  const { data: dc, isLoading } = useQuery<DentureCase>({
    queryKey: ['denture-case', caseId],
    queryFn: () => fetcher<DentureCase>(`/api/v2/clinical/denture-cases/${caseId}`),
    enabled: open && !!caseId,
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['denture-case', caseId] });
    onChanged();
  };

  const advanceMut = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/clinical/denture-cases/${caseId}/advance`, {
        method: 'POST',
        body: JSON.stringify({}),
      }),
    onSuccess: invalidate,
  });

  const closeMut = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/clinical/denture-cases/${caseId}/close`, {
        method: 'POST',
        body: JSON.stringify({}),
      }),
    onSuccess: () => {
      invalidate();
      onClose();
    },
  });

  return (
    <Drawer open={open} onClose={onClose} title={`Denture Case #${caseId ?? ''}`} width="md">
      {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}
      {dc && (
        <div className="space-y-2 text-sm">
          <div><span className="text-zinc-500">Patient: </span>{dc.patient_id}</div>
          <div><span className="text-zinc-500">Arch: </span>{dc.arch}</div>
          <div><span className="text-zinc-500">Type: </span>{dc.case_type}</div>
          <div><span className="text-zinc-500">Stage: </span>{dc.current_stage}</div>
          <div><span className="text-zinc-500">Status: </span>{dc.status}</div>
          {dc.notes && <div><span className="text-zinc-500">Notes: </span>{dc.notes}</div>}
          <div className="flex gap-2 border-t border-zinc-100 pt-3">
            <button
              onClick={() => advanceMut.mutate()}
              disabled={advanceMut.isPending || dc.status === 'closed'}
              className="rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700 disabled:opacity-40"
            >
              Advance stage
            </button>
            <button
              onClick={() => closeMut.mutate()}
              disabled={closeMut.isPending || dc.status === 'closed'}
              className="rounded border border-zinc-300 px-3 py-1 text-xs hover:bg-zinc-50 disabled:opacity-40"
            >
              Close
            </button>
          </div>
          {advanceMut.error && (
            <p className="text-xs text-red-600">{(advanceMut.error as Error).message}</p>
          )}
        </div>
      )}
    </Drawer>
  );
}
