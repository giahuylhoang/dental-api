import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Phone, Mail } from 'lucide-react';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import { useNavigate } from 'react-router-dom';
import LeadCreateDialog from './LeadCreateDialog';
import LeadDrawer from './LeadDrawer';
import { Skeleton } from '../../components/ui/skeleton';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardHeader, CardContent, CardFooter } from '../../components/ui/card';
import { PageHeader } from '../../components/ui/page-header';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '../../components/ui/dropdown-menu';

type LeadStatus = 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'CONVERTED' | 'LOST';

interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  status: LeadStatus;
  source: string | null;
  notes: string | null;
  clinic_id: string;
}

const COLUMNS: LeadStatus[] = ['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'];

const COL_COLORS: Record<LeadStatus, string> = {
  NEW: 'bg-zinc-400',
  CONTACTED: 'bg-blue-400',
  QUALIFIED: 'bg-yellow-400',
  CONVERTED: 'bg-green-400',
  LOST: 'bg-red-400',
};

const COL_BG: Record<LeadStatus, string> = {
  NEW: 'bg-zinc-50',
  CONTACTED: 'bg-blue-50',
  QUALIFIED: 'bg-yellow-50',
  CONVERTED: 'bg-green-50',
  LOST: 'bg-red-50',
};

function SkeletonColumn() {
  return (
    <div className="flex w-64 shrink-0 flex-col rounded-lg border border-zinc-200 bg-zinc-50">
      <div className="border-b border-zinc-200 px-3 py-2">
        <Skeleton className="h-3 w-20" />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-2">
        {[0, 1].map((i) => (
          <Skeleton key={i} data-testid="lead-skeleton" className="h-24" />
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

  const activeCount = leads.filter(
    (l) => l.status !== 'CONVERTED' && l.status !== 'LOST',
  ).length;

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="CRM"
          description="Loading…"
          actions={<Button>+ New lead</Button>}
        />
        <div className="flex gap-3 overflow-x-auto pb-4">
          {COLUMNS.map((col) => <SkeletonColumn key={col} />)}
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="CRM"
        description={`${activeCount} active leads`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>+ New lead</Button>
        }
      />
      <div className="flex gap-3 overflow-x-auto pb-4">
        {COLUMNS.map((col) => {
          const colLeads = leads.filter((l) => l.status === col);
          return (
            <div
              key={col}
              className={`flex w-64 shrink-0 flex-col rounded-lg border border-zinc-200 ${COL_BG[col]}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (dragging) updateStatus.mutate({ id: dragging, status: col });
                setDragging(null);
              }}
            >
              {/* Sticky column header */}
              <div className="sticky top-0 z-10 flex items-center gap-2 border-b border-zinc-200 bg-inherit px-3 py-2">
                <span
                  className={`inline-block h-2.5 w-2.5 rounded-full ${COL_COLORS[col]}`}
                  aria-hidden="true"
                />
                <span className="text-xs font-semibold uppercase tracking-wide text-zinc-600">
                  {col} ({colLeads.length})
                </span>
              </div>

              <div className="flex flex-1 flex-col gap-2 p-2">
                {colLeads.length === 0 && (
                  <div className="py-6 text-center text-xs text-zinc-400">
                    Drop leads here
                  </div>
                )}
                {colLeads.map((lead) => (
                  <Card
                    key={lead.id}
                    draggable
                    onDragStart={() => setDragging(lead.id)}
                    onDragEnd={() => setDragging(null)}
                    className="cursor-pointer"
                    onClick={() => setDrawerLeadId(lead.id)}
                  >
                    <CardHeader className="p-3 pb-1">
                      <div className="flex items-start justify-between gap-1">
                        <span className="text-sm font-medium">
                          {lead.first_name} {lead.last_name}
                        </span>
                        {lead.source && (
                          <Badge variant="secondary" className="shrink-0 text-xs">
                            {lead.source}
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="px-3 pb-1 pt-0">
                      {lead.phone && (
                        <div className="flex items-center gap-1 text-xs text-zinc-500">
                          <Phone className="h-3 w-3" />
                          {lead.phone}
                        </div>
                      )}
                      {lead.email && (
                        <div className="flex items-center gap-1 text-xs text-zinc-500">
                          <Mail className="h-3 w-3" />
                          {lead.email}
                        </div>
                      )}
                      {lead.notes && (
                        <p className="mt-1 line-clamp-2 text-xs text-zinc-500">
                          {lead.notes}
                        </p>
                      )}
                    </CardContent>
                    <CardFooter className="px-3 pb-2 pt-1">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 w-full text-xs"
                            onClick={(e) => e.stopPropagation()}
                          >
                            Actions ▾
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent onClick={(e) => e.stopPropagation()}>
                          <DropdownMenuItem
                            onSelect={() => convert.mutate(lead.id)}
                            disabled={convert.isPending}
                          >
                            Convert
                          </DropdownMenuItem>
                          <DropdownMenuItem onSelect={() => setDrawerLeadId(lead.id)}>
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onSelect={() => setDrawerLeadId(lead.id)}>
                            Add activity
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onSelect={() =>
                              updateStatus.mutate({ id: lead.id, status: 'LOST' })
                            }
                          >
                            Archive
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      <LeadCreateDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      {drawerLeadId && (
        <LeadDrawer
          open={!!drawerLeadId}
          onClose={() => setDrawerLeadId(null)}
          leadId={drawerLeadId}
        />
      )}
    </>
  );
}
