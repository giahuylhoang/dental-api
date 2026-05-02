import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import { useNavigate } from 'react-router-dom';
import LeadCreateDialog from './LeadCreateDialog';
import LeadDrawer from './LeadDrawer';
import { Skeleton } from '../../components/ui/skeleton';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';

type LeadStatus = 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'CONVERTED' | 'LOST';

interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  status: LeadStatus;
  source: string | null;
  clinic_id: string;
}

const COLUMNS: LeadStatus[] = ['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'];

const COL_COLORS: Record<LeadStatus, string> = {
  NEW: 'bg-zinc-50',
  CONTACTED: 'bg-blue-50',
  QUALIFIED: 'bg-yellow-50',
  CONVERTED: 'bg-green-50',
  LOST: 'bg-red-50',
};

const SOURCE_ICONS: Record<string, string> = {
  phone: '📞',
  web: '🌐',
  referral: '👥',
  'walk-in': '🚶',
};

function sourcePill(source: string | null) {
  if (!source) return null;
  const icon = SOURCE_ICONS[source] ?? '❓';
  return (
    <Badge variant="secondary" className="mt-1">
      {icon} {source}
    </Badge>
  );
}

function SkeletonColumn() {
  return (
    <div className="flex w-56 shrink-0 flex-col rounded-lg border border-zinc-200 bg-zinc-50">
      <div className="border-b border-zinc-200 px-3 py-2">
        <Skeleton className="h-3 w-20" />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-2">
        {[0, 1].map((i) => (
          <Skeleton
            key={i}
            data-testid="lead-skeleton"
            className="h-16"
          />
        ))}
      </div>
    </div>
  );
}

export default function LeadKanban() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [dragging, setDragging] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [drawerLeadId, setDrawerLeadId] = useState<string | null>(null);

  const { data: leads = [], isLoading } = useQuery<Lead[]>({
    queryKey: ['leads', clinicId],
    queryFn: () => fetcher<Lead[]>('/api/v2/crm/leads'),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: LeadStatus }) =>
      fetcher(`/api/v2/crm/leads/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ status }),
      }),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: ['leads', clinicId] });
      const prev = qc.getQueryData<Lead[]>(['leads', clinicId]);
      qc.setQueryData<Lead[]>(['leads', clinicId], (old) =>
        old?.map((l) => (l.id === id ? { ...l, status } : l)) ?? [],
      );
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(['leads', clinicId], ctx.prev);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['leads', clinicId] }),
  });

  const convert = useMutation({
    mutationFn: (id: string) =>
      fetcher<{ patient_id: string }>(`/api/v2/crm/leads/${id}/convert`, {
        method: 'POST',
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['leads', clinicId] });
      qc.invalidateQueries({ queryKey: ['patients'] });
      navigate(`/patients/${data.patient_id}`);
    },
  });

  if (isLoading) {
    return (
      <>
        <div className="mb-3 flex justify-end">
          <Button size="sm">+ New Lead</Button>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-4">
          {COLUMNS.map((col) => <SkeletonColumn key={col} />)}
        </div>
      </>
    );
  }

  return (
    <>
      <div className="mb-3 flex justify-end">
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          + New Lead
        </Button>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-4">
      {COLUMNS.map((col) => {
        const colLeads = leads.filter((l) => l.status === col);
        return (
          <div
            key={col}
            className={`flex w-56 shrink-0 flex-col rounded-lg border border-zinc-200 ${COL_COLORS[col]}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (dragging) updateStatus.mutate({ id: dragging, status: col });
              setDragging(null);
            }}
          >
            <div className="border-b border-zinc-200 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-600">
              {col} ({colLeads.length})
            </div>
            <div className="flex flex-1 flex-col gap-2 p-2">
              {colLeads.map((lead) => (
                <div
                  key={lead.id}
                  draggable
                  onDragStart={() => setDragging(lead.id)}
                  onDragEnd={() => setDragging(null)}
                  onClick={() => setDrawerLeadId(lead.id)}
                  className="cursor-pointer rounded bg-white p-3 shadow-sm"
                >
                  <div className="text-sm font-medium">
                    {lead.first_name} {lead.last_name}
                  </div>
                  {lead.phone && (
                    <div className="text-xs text-zinc-500">{lead.phone}</div>
                  )}
                  {sourcePill(lead.source)}
                  {col !== 'CONVERTED' && col !== 'LOST' && (
                    <Button
                      size="sm"
                      variant="secondary"
                      className="mt-2 w-full text-xs"
                      onClick={(e) => { e.stopPropagation(); convert.mutate(lead.id); }}
                      disabled={convert.isPending}
                    >
                      Convert →
                    </Button>
                  )}
                </div>
              ))}
              {colLeads.length === 0 && (
                <div className="py-4 text-center text-xs text-zinc-400">Empty</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
      <LeadCreateDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      {drawerLeadId && (
        <LeadDrawer open={!!drawerLeadId} onClose={() => setDrawerLeadId(null)} leadId={drawerLeadId} />
      )}
    </>
  );
}
