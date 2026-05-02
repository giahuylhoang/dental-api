import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import Drawer from '../../components/Drawer';
import AdjudicateForm from './AdjudicateForm';

interface Claim {
  id: string;
  invoice_id: string;
  carrier: string;
  kind: string;
  status: 'draft' | 'submitted' | 'adjudicated' | 'paid';
  response_codes?: string[];
  submitted_at?: string;
  adjudicated_at?: string;
  outcome?: string;
  accepted_amount_cents?: number;
  notes?: string;
  created_at: string;
}

interface Props {
  claimId: string | null;
  open: boolean;
  onClose: () => void;
  onChanged?: () => void;
}

const STATUS_STEPS = ['draft', 'submitted', 'adjudicated', 'paid'] as const;

export default function ClaimDrawer({ claimId, open, onClose, onChanged }: Props) {
  const qc = useQueryClient();

  const { data: claim, isLoading } = useQuery<Claim>({
    queryKey: ['claim', claimId],
    queryFn: () => fetcher<Claim>(`/api/v2/insurance/claims/${claimId}`),
    enabled: !!claimId && open,
  });

  const submit = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/insurance/claims/${claimId}/submit`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['claim', claimId] });
      onChanged?.();
    },
  });

  const markPaid = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/insurance/claims/${claimId}/mark-paid`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['claim', claimId] });
      onChanged?.();
    },
  });

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={`Claim ${claimId?.slice(0, 8) ?? ''}`}
      width="md"
      footer={
        <div className="flex gap-2">
          {claim?.status === 'draft' && (
            <button
              disabled={submit.isPending}
              onClick={() => submit.mutate()}
              className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submit.isPending ? 'Submitting…' : 'Submit'}
            </button>
          )}
          {claim?.status === 'adjudicated' && (
            <button
              disabled={markPaid.isPending}
              onClick={() => markPaid.mutate()}
              className="rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
            >
              {markPaid.isPending ? 'Saving…' : 'Mark Paid'}
            </button>
          )}
          <button
            onClick={onClose}
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
          >
            Close
          </button>
        </div>
      }
    >
      {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}
      {claim && (
        <div className="space-y-4">
          {/* Status timeline */}
          <div>
            <h3 className="mb-2 text-xs font-semibold uppercase text-zinc-500">Status</h3>
            <div className="flex items-center gap-1">
              {STATUS_STEPS.map((step, i) => {
                const idx = STATUS_STEPS.indexOf(claim.status);
                const done = i <= idx;
                return (
                  <div key={step} className="flex items-center gap-1">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${done ? 'bg-blue-600 text-white' : 'bg-zinc-100 text-zinc-400'}`}
                    >
                      {step}
                    </span>
                    {i < STATUS_STEPS.length - 1 && (
                      <span className="text-zinc-300">→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Details */}
          <div className="space-y-1 text-sm">
            <div><span className="text-zinc-500">Carrier:</span> {claim.carrier}</div>
            <div><span className="text-zinc-500">Kind:</span> {claim.kind}</div>
            {claim.outcome && (
              <div><span className="text-zinc-500">Outcome:</span> {claim.outcome}</div>
            )}
            {claim.accepted_amount_cents != null && (
              <div>
                <span className="text-zinc-500">Accepted:</span>{' '}
                ${(claim.accepted_amount_cents / 100).toFixed(2)}
              </div>
            )}
          </div>

          {/* Response codes */}
          {claim.response_codes && claim.response_codes.length > 0 && (
            <div>
              <h3 className="mb-1 text-xs font-semibold uppercase text-zinc-500">Response Codes</h3>
              <ul className="space-y-0.5">
                {claim.response_codes.map((code) => (
                  <li key={code} className="rounded bg-zinc-50 px-2 py-1 font-mono text-xs">
                    {code}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Adjudication form */}
          {claim.status === 'submitted' && (
            <AdjudicateForm
              claimId={claim.id}
              onSaved={() => onChanged?.()}
            />
          )}
        </div>
      )}
    </Drawer>
  );
}
