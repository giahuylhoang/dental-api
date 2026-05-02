import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import FormField from '../../components/forms/FormField';

interface Props {
  claimId: string;
  onSaved: () => void;
}

export default function AdjudicateForm({ claimId, onSaved }: Props) {
  const qc = useQueryClient();
  const [outcome, setOutcome] = useState<'accepted' | 'rejected' | 'partial'>('accepted');
  const [amount, setAmount] = useState('');
  const [notes, setNotes] = useState('');

  const mutate = useMutation({
    mutationFn: () =>
      fetcher(`/api/v2/insurance/claims/${claimId}/adjudicate`, {
        method: 'POST',
        body: JSON.stringify({
          outcome,
          accepted_amount_cents: outcome !== 'rejected' ? Math.round(parseFloat(amount) * 100) : undefined,
          notes: notes || undefined,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['claim', claimId] });
      onSaved();
    },
  });

  return (
    <div className="space-y-3 rounded border border-zinc-200 p-3">
      <h4 className="text-sm font-semibold">Adjudicate Claim</h4>
      <FormField label="Outcome" name="outcome">
        <select
          id="outcome"
          className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
          value={outcome}
          onChange={(e) => setOutcome(e.target.value as typeof outcome)}
        >
          <option value="accepted">Accepted</option>
          <option value="partial">Partial</option>
          <option value="rejected">Rejected</option>
        </select>
      </FormField>
      {outcome !== 'rejected' && (
        <FormField label="Accepted Amount ($)" name="accepted_amount_cents">
          <input
            id="accepted_amount_cents"
            type="number"
            min="0"
            step="0.01"
            className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </FormField>
      )}
      <FormField label="Notes" name="notes">
        <textarea
          id="notes"
          className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm"
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </FormField>
      {mutate.error && (
        <p className="text-xs text-red-600">{(mutate.error as Error).message}</p>
      )}
      <button
        disabled={mutate.isPending || (outcome !== 'rejected' && !amount)}
        onClick={() => mutate.mutate()}
        className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {mutate.isPending ? 'Saving…' : 'Submit Adjudication'}
      </button>
    </div>
  );
}
