import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../../api/client';

const STAGES = [
  { key: 'consult', label: 'Consultation' },
  { key: 'prelim_imp', label: 'Preliminary Impressions' },
  { key: 'final_imp', label: 'Final Impressions' },
  { key: 'bite_reg', label: 'Bite Registration' },
  { key: 'wax_tryin', label: 'Wax Try-In' },
  { key: 'insert', label: 'Insert' },
  { key: 'adjust', label: 'Adjustments' },
  { key: 'complete', label: 'Complete' },
];

interface DentureCase {
  id: string;
  patient_id: string;
  arch: string;
  case_type: string;
  current_stage: string;
  status: string;
}

interface DentureCaseEvent {
  id: string;
  case_id: string;
  stage: string;
  occurred_at: string;
  note: string | null;
}

interface DentureCaseTimelineProps {
  caseId: string;
}

export default function DentureCaseTimeline({ caseId }: DentureCaseTimelineProps) {
  const qc = useQueryClient();
  const [showAdvance, setShowAdvance] = useState(false);
  const [advanceNote, setAdvanceNote] = useState('');

  const { data: dc } = useQuery<DentureCase>({
    queryKey: ['denture-case', caseId],
    queryFn: () => fetcher<DentureCase>(`/api/v2/clinical/denture-cases/${caseId}`),
  });

  const { data: events } = useQuery<DentureCaseEvent[]>({
    queryKey: ['denture-case-events', caseId],
    queryFn: () => fetcher<DentureCaseEvent[]>(`/api/v2/clinical/denture-cases/${caseId}/events`),
  });

  const advance = useMutation({
    mutationFn: (note: string) =>
      fetcher(`/api/v2/clinical/denture-cases/${caseId}/advance`, {
        method: 'POST',
        body: JSON.stringify({ note }),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['denture-case', caseId] });
      void qc.invalidateQueries({ queryKey: ['denture-case-events', caseId] });
      setShowAdvance(false);
      setAdvanceNote('');
    },
  });

  const currentIdx = STAGES.findIndex((s) => s.key === dc?.current_stage);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">
          {dc?.arch} / {dc?.case_type}
        </h3>
        {dc?.status === 'open' && (
          <button
            onClick={() => setShowAdvance(true)}
            className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700"
          >
            Advance Stage
          </button>
        )}
      </div>

      <ol className="relative border-l border-zinc-200 pl-6">
        {STAGES.map((stage, idx) => {
          const isPast = idx < currentIdx;
          const isCurrent = idx === currentIdx;
          const event = events?.find((e) => e.stage === stage.key);
          return (
            <li key={stage.key} className="mb-4">
              <span
                className={`absolute -left-2 flex h-4 w-4 items-center justify-center rounded-full border-2 ${
                  isCurrent
                    ? 'border-zinc-900 bg-zinc-900'
                    : isPast
                    ? 'border-zinc-400 bg-zinc-400'
                    : 'border-zinc-200 bg-white'
                }`}
              />
              <p className={`text-sm font-medium ${isCurrent ? 'text-zinc-900' : isPast ? 'text-zinc-500' : 'text-zinc-300'}`}>
                {stage.label}
              </p>
              {event && (
                <p className="text-xs text-zinc-400">
                  {new Date(event.occurred_at).toLocaleDateString()}
                  {event.note && ` — ${event.note}`}
                </p>
              )}
            </li>
          );
        })}
      </ol>

      {showAdvance && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
            <h4 className="mb-3 font-medium">Advance Stage</h4>
            <textarea
              value={advanceNote}
              onChange={(e) => setAdvanceNote(e.target.value)}
              placeholder="Add a note (optional)…"
              rows={3}
              className="mb-4 w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAdvance(false)}
                className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={() => advance.mutate(advanceNote)}
                disabled={advance.isPending}
                className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white disabled:opacity-50"
              >
                Advance
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
