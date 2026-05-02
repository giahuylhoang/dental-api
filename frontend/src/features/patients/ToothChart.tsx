import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import type { components } from '../../api/v2/types';

type ToothChartEntry = components['schemas']['ToothChartEntry'];
type ToothChartEntryIn = components['schemas']['ToothChartEntryIn'];

type ToothStatus = 'present' | 'missing' | 'extracted' | 'implant' | 'crowned' | 'filled';

const STATUS_OPTIONS: ToothStatus[] = ['present', 'missing', 'extracted', 'implant', 'crowned', 'filled'];

const STATUS_COLOR: Record<ToothStatus, string> = {
  present: '#d4d4d8',
  missing: 'transparent',
  extracted: '#ef4444',
  implant: '#3b82f6',
  crowned: '#eab308',
  filled: '#06b6d4',
};

const STATUS_STROKE: Record<ToothStatus, string> = {
  present: '#a1a1aa',
  missing: '#a1a1aa',
  extracted: '#ef4444',
  implant: '#2563eb',
  crowned: '#ca8a04',
  filled: '#0891b2',
};

// Maxillary 1-16 (top row, right to left: 1-8 then 9-16)
// Mandibular 17-32 (bottom row, left to right: 17-24 then 25-32)
const TOP_ROW = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
const BOTTOM_ROW = [32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17];

interface ToothChartProps {
  patientId: string;
  onToothClick?: (toothNumber: number) => void;
  highlightedTeeth?: (number | null | undefined)[];
}

interface Popover {
  toothNumber: number;
  status: ToothStatus;
  notes: string;
}

export default function ToothChart({ patientId, onToothClick, highlightedTeeth = [] }: ToothChartProps) {
  const qc = useQueryClient();
  const [popover, setPopover] = useState<Popover | null>(null);

  const { data: chart = [], isLoading } = useQuery<ToothChartEntry[]>({
    queryKey: ['tooth-chart', patientId],
    queryFn: () => fetcher<ToothChartEntry[]>(`/api/v2/clinical/patients/${patientId}/tooth-chart`),
  });

  const saveMutation = useMutation({
    mutationFn: (entry: ToothChartEntryIn) =>
      fetcher<ToothChartEntry[]>(`/api/v2/clinical/patients/${patientId}/tooth-chart`, {
        method: 'POST',
        body: JSON.stringify([entry]),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['tooth-chart', patientId] });
      setPopover(null);
    },
  });

  function getEntry(n: number): ToothChartEntry {
    return chart.find((e) => e.tooth_number === n) ?? { tooth_number: n, status: 'present' };
  }

  function handleToothClick(n: number) {
    if (onToothClick) {
      onToothClick(n);
      return;
    }
    const entry = getEntry(n);
    setPopover({
      toothNumber: n,
      status: (entry.status as ToothStatus) ?? 'present',
      notes: (entry.surface_notes as Record<string, string> | null)?.notes ?? '',
    });
  }

  function renderTooth(n: number) {
    const entry = getEntry(n);
    const status = (entry.status as ToothStatus) ?? 'present';
    const fill = STATUS_COLOR[status];
    const stroke = STATUS_STROKE[status];
    const dashArray = status === 'extracted' ? '3,2' : undefined;
    const isHighlighted = highlightedTeeth.includes(n);

    return (
      <g
        key={n}
        onClick={() => handleToothClick(n)}
        style={{ cursor: 'pointer' }}
        data-tooth={n}
      >
        <rect
          width={20}
          height={24}
          rx={3}
          fill={fill}
          stroke={stroke}
          strokeWidth={1.5}
          strokeDasharray={dashArray}
        />
        <text x={10} y={16} textAnchor="middle" fontSize={8} fill="#52525b">
          {n}
        </text>
        {isHighlighted && (
          <circle cx={17} cy={3} r={3} fill="#f97316" />
        )}
      </g>
    );
  }

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  const toothW = 22;
  const svgW = 16 * toothW + 10;

  return (
    <div className="space-y-4">
      <svg width={svgW} height={80} viewBox={`0 0 ${svgW} 80`} className="w-full max-w-2xl">
        {/* Top row */}
        {TOP_ROW.map((n, i) => (
          <g key={n} transform={`translate(${5 + i * toothW}, 4)`}>
            {renderTooth(n)}
          </g>
        ))}
        {/* Bottom row */}
        {BOTTOM_ROW.map((n, i) => (
          <g key={n} transform={`translate(${5 + i * toothW}, 50)`}>
            {renderTooth(n)}
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-zinc-600">
        {STATUS_OPTIONS.map((s) => (
          <div key={s} className="flex items-center gap-1">
            <span
              className="inline-block h-3 w-3 rounded-sm border"
              style={{ background: STATUS_COLOR[s], borderColor: STATUS_STROKE[s] }}
            />
            {s}
          </div>
        ))}
      </div>

      {/* Popover */}
      {popover && (
        <div className="rounded border border-zinc-200 bg-white p-4 shadow-md">
          <h4 className="mb-3 text-sm font-medium">Tooth #{popover.toothNumber}</h4>
          <div className="space-y-3">
            <div>
              <label htmlFor="tooth-status" className="mb-1 block text-xs text-zinc-600">Status</label>
              <select
                id="tooth-status"
                value={popover.status}
                onChange={(e) => setPopover((p) => p ? { ...p, status: e.target.value as ToothStatus } : p)}
                className="rounded border border-zinc-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="tooth-notes" className="mb-1 block text-xs text-zinc-600">Notes</label>
              <input
                id="tooth-notes"
                value={popover.notes}
                onChange={(e) => setPopover((p) => p ? { ...p, notes: e.target.value } : p)}
                className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() =>
                  saveMutation.mutate({
                    tooth_number: popover.toothNumber,
                    status: popover.status,
                    surface_notes: popover.notes ? (({ notes: popover.notes } as unknown) as Record<string, never>) : null,
                  })
                }
                disabled={saveMutation.isPending}
                className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-50"
              >
                Save
              </button>
              <button
                onClick={() => setPopover(null)}
                className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
