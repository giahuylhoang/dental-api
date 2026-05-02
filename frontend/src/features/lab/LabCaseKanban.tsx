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
import { CalendarIcon, GripVertical } from 'lucide-react';
import { fetcher } from '../../api/client';
import LabCaseDrawer from './LabCaseDrawer';
import LabCaseCreateForm from './LabCaseCreateForm';
import { PatientChip } from '../patients/PatientChip';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';
import { PageHeader } from '@/components/ui/page-header';

const COLUMNS = ['draft', 'sent', 'in_progress', 'returned', 'remake'] as const;
type LabStatus = (typeof COLUMNS)[number];

const LABELS: Record<LabStatus, string> = {
  draft: 'Draft',
  sent: 'Sent',
  in_progress: 'In Progress',
  returned: 'Returned',
  remake: 'Remake',
};

const STATUS_VARIANT: Record<LabStatus, 'default' | 'secondary' | 'outline' | 'warning' | 'destructive'> = {
  draft: 'secondary',
  sent: 'default',
  in_progress: 'warning',
  returned: 'outline',
  remake: 'destructive',
};

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

function KanbanCard({
  labCase,
  onClick,
  onAction,
}: {
  labCase: LabCase;
  onClick: () => void;
  onAction: (action: string) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: labCase.id,
  });
  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined;

  return (
    <Card
      ref={setNodeRef}
      style={style}
      className={`cursor-pointer group ${isDragging ? 'opacity-50' : ''}`}
      onClick={onClick}
    >
      <CardHeader className="p-3 pb-1 flex-row items-center justify-between space-y-0">
        <span className="font-mono text-xs text-zinc-600">
          {labCase.case_number ?? `#${labCase.id}`}
        </span>
        <div className="flex items-center gap-1">
          <Badge variant={STATUS_VARIANT[labCase.status] ?? 'secondary'}>
            {LABELS[labCase.status]}
          </Badge>
          {/* drag handle */}
          <span
            {...listeners}
            {...attributes}
            onClick={(e) => e.stopPropagation()}
            className="cursor-grab opacity-0 group-hover:opacity-100 transition-opacity text-zinc-400 hover:text-zinc-600"
            aria-label="drag handle"
          >
            <GripVertical className="h-4 w-4" />
          </span>
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-1 space-y-1">
        {labCase.patient_id && (
          <PatientChip patientId={labCase.patient_id} variant="inline" />
        )}
        {labCase.due_back_at && (
          <p className="flex items-center gap-1 text-xs text-zinc-400">
            <CalendarIcon className="h-3 w-3" />
            {new Date(labCase.due_back_at).toLocaleDateString()}
          </p>
        )}
      </CardContent>
      <CardFooter className="p-3 pt-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="outline" size="sm" className="h-6 text-xs">
              Actions
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={() => onAction('send')}>Send</DropdownMenuItem>
            <DropdownMenuItem onSelect={() => onAction('return')}>Mark returned</DropdownMenuItem>
            <DropdownMenuItem onSelect={() => onAction('remake')}>Request remake</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardFooter>
    </Card>
  );
}

function KanbanColumn({
  status,
  cases,
  onCardClick,
  onAction,
}: {
  status: LabStatus;
  cases: LabCase[];
  onCardClick: (id: string) => void;
  onAction: (caseId: string, action: string) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-48 w-52 flex-col gap-2 rounded-lg border border-zinc-200 p-3 ${isOver ? 'bg-zinc-100' : 'bg-zinc-50'}`}
    >
      <h3 className="sticky top-0 mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500 bg-zinc-50 py-1">
        {LABELS[status]} ({cases.length})
      </h3>
      {cases.map((c) => (
        <KanbanCard
          key={c.id}
          labCase={c}
          onClick={() => onCardClick(c.id)}
          onAction={(action) => onAction(c.id, action)}
        />
      ))}
    </div>
  );
}

export default function LabCaseKanban() {
  const qc = useQueryClient();
  const [remakeDialog, setRemakeDialog] = useState<{ caseId: string } | null>(null);
  const [remakeReason, setRemakeReason] = useState('');
  const [drawerCaseId, setDrawerCaseId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const { data: cases = [] } = useQuery<LabCase[]>({
    queryKey: ['lab-cases'],
    queryFn: () => fetcher<LabCase[]>('/api/v2/lab/cases'),
  });

  const activeCases = cases.filter((c) => c.status !== 'returned' && c.status !== 'remake');

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

  function handleAction(caseId: string, action: string) {
    if (action === 'remake') {
      setRemakeDialog({ caseId });
    } else if (action === 'send') {
      updateStatus.mutate({ id: caseId, status: 'sent' });
    } else if (action === 'return') {
      updateStatus.mutate({ id: caseId, status: 'returned' });
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
      <PageHeader
        title="Lab"
        description={`${activeCases.length} active cases`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>+ New case</Button>
        }
      />

      {/* Status legend */}
      <div className="mb-4 flex flex-wrap gap-2">
        {COLUMNS.map((col) => (
          <Badge key={col} variant={STATUS_VARIANT[col] ?? 'secondary'}>
            {LABELS[col]}
          </Badge>
        ))}
      </div>

      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <KanbanColumn
              key={col}
              status={col}
              cases={cases.filter((c) => c.status === col)}
              onCardClick={(id) => setDrawerCaseId(id)}
              onAction={handleAction}
            />
          ))}
        </div>
      </DndContext>

      {/* Remake reason dialog */}
      <Dialog open={!!remakeDialog} onOpenChange={(open) => !open && setRemakeDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remake Reason</DialogTitle>
          </DialogHeader>
          <textarea
            value={remakeReason}
            onChange={(e) => setRemakeReason(e.target.value)}
            placeholder="Describe the reason for remake…"
            rows={3}
            className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setRemakeDialog(null)}>Cancel</Button>
            <Button onClick={confirmRemake}>Confirm Remake</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* New case dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Lab Case</DialogTitle>
          </DialogHeader>
          <LabCaseCreateForm
            onCreated={() => {
              setCreateOpen(false);
              void qc.invalidateQueries({ queryKey: ['lab-cases'] });
            }}
          />
        </DialogContent>
      </Dialog>

      <LabCaseDrawer
        caseId={drawerCaseId}
        open={drawerCaseId !== null}
        onClose={() => setDrawerCaseId(null)}
        onChanged={() => void qc.invalidateQueries({ queryKey: ['lab-cases'] })}
      />
    </div>
  );
}
