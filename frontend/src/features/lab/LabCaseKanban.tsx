import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DndContext,
  type DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useDroppable, useDraggable } from '@dnd-kit/core';
import { fetcher } from '../../api/client';
import LabCaseDrawer from './LabCaseDrawer';
import { PatientChip } from '../patients/PatientChip';

const COLUMNS = ['draft', 'sent', 'in_progress', 'returned', 'remake'] as const;
type LabStatus = (typeof COLUMNS)[number];

interface LabCase {
  id: string;
  case_number?: string;
  denture_case_id: string;
  vendor_id: string;
  status: LabStatus;
  sent_at: string | null;
  due_back_at: string | null;
  lab_fee: number | null;
  remake_of_id: string | null;
  remake_reason: string | null;
  treatment_plan_id?: string | null;
  patient_id?: string | null;
}

function KanbanCard({ labCase, onClick }: { labCase: LabCase; onClick: () => void }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: labCase.id,
  });
  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined;
  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={onClick}
      className={`cursor-grab rounded border border-zinc-200 bg-white p-3 text-sm shadow-sm ${isDragging ? 'opacity-50' : ''}`}
    >
      {labCase.patient_id && (
        <div className="mb-1">
          <PatientChip patientId={labCase.patient_id} />
        </div>
      )}
      {labCase.case_number && (
        <span className="mb-1 inline-block rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-600">
          {labCase.case_number}
        </span>
      )}
      <p className="font-medium">Case #{labCase.id}</p>
      {labCase.lab_fee != null && <p className="text-zinc-500">${labCase.lab_fee}</p>}
      {labCase.due_back_at && (
        <p className="text-xs text-zinc-400">Due: {new Date(labCase.due_back_at).toLocaleDateString()}</p>
      )}
      {labCase.remake_of_id && (
        <p className="text-xs text-amber-600">Remake of #{labCase.remake_of_id}</p>
      )}
    </div>
  );
}

function KanbanColumn({
  status,
  cases,
  onCardClick,
}: {
  status: LabStatus;
  cases: LabCase[];
  onCardClick: (id: string) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const labels: Record<LabStatus, string> = {
    draft: 'Draft',
    sent: 'Sent',
    in_progress: 'In Progress',
    returned: 'Returned',
    remake: 'Remake',
  };
  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-48 w-48 flex-col gap-2 rounded-lg border border-zinc-200 p-3 ${isOver ? 'bg-zinc-100' : 'bg-zinc-50'}`}
    >
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        {labels[status]} ({cases.length})
      </h3>
      {cases.map((c) => (
        <KanbanCard key={c.id} labCase={c} onClick={() => onCardClick(c.id)} />
      ))}
    </div>
  );
}

export default function LabCaseKanban() {
  const qc = useQueryClient();
  const [remakeDialog, setRemakeDialog] = useState<{ caseId: string } | null>(null);
  const [remakeReason, setRemakeReason] = useState('');
  const [drawerCaseId, setDrawerCaseId] = useState<string | null>(null);

  const { data: cases = [] } = useQuery<LabCase[]>({
    queryKey: ['lab-cases'],
    queryFn: () => fetcher<LabCase[]>('/api/v2/lab/cases'),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status, remake_reason }: { id: string; status: string; remake_reason?: string }) =>
      fetcher(`/api/v2/lab/cases/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, remake_reason }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['lab-cases'] }),
  });

  const sensors = useSensors(useSensor(PointerSensor));

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const newStatus = over.id as LabStatus;
    if (newStatus === 'remake') {
      setRemakeDialog({ caseId: String(active.id) });
    } else {
      updateStatus.mutate({ id: String(active.id), status: newStatus });
    }
  }

  function confirmRemake() {
    if (!remakeDialog) return;
    updateStatus.mutate({ id: remakeDialog.caseId, status: 'remake', remake_reason: remakeReason });
    setRemakeDialog(null);
    setRemakeReason('');
  }

  return (
    <div>
      <h2 className="mb-4 text-xl font-semibold">Lab Cases</h2>
      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <KanbanColumn
              key={col}
              status={col}
              cases={cases.filter((c) => c.status === col)}
              onCardClick={(id) => setDrawerCaseId(id)}
            />
          ))}
        </div>
      </DndContext>

      {remakeDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
            <h4 className="mb-3 font-medium">Remake Reason</h4>
            <textarea
              value={remakeReason}
              onChange={(e) => setRemakeReason(e.target.value)}
              placeholder="Describe the reason for remake…"
              rows={3}
              className="mb-4 w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setRemakeDialog(null)}
                className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={confirmRemake}
                className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white"
              >
                Confirm Remake
              </button>
            </div>
          </div>
        </div>
      )}

      <LabCaseDrawer
        caseId={drawerCaseId}
        open={drawerCaseId !== null}
        onClose={() => setDrawerCaseId(null)}
        onChanged={() => void qc.invalidateQueries({ queryKey: ['lab-cases'] })}
      />
    </div>
  );
}
