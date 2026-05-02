import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '../../components/ui/sheet';
import { Button } from '../../components/ui/button';
import LeadActivityTimeline from './LeadActivityTimeline';
import AddActivityForm from './AddActivityForm';

type LeadStatus = 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'CONVERTED' | 'LOST';
const STATUSES: LeadStatus[] = ['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'];

interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  status: LeadStatus;
  source: string | null;
  notes: string | null;
  owner_id: string | null;
  clinic_id: string;
}

interface Provider {
  id: string;
  name: string;
  is_active?: boolean;
}

interface Activity {
  id: string;
  kind: string;
  body: string;
  author?: string;
  created_at: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  leadId: string;
}

type Tab = 'detail' | 'activities' | 'convert';
const TABS: Tab[] = ['detail', 'activities', 'convert'];

export default function LeadDrawer({ open, onClose, leadId }: Props) {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>('detail');

  const { data: lead } = useQuery<Lead>({
    queryKey: ['lead', leadId],
    queryFn: () => fetcher<Lead>(`/api/v2/crm/leads/${leadId}`),
    enabled: open && !!leadId,
  });

  const { data: providers = [] } = useQuery<Provider[]>({
    queryKey: ['providers'],
    queryFn: () => fetcher<Provider[]>('/api/providers'),
    enabled: open,
  });

  const { data: activities = [] } = useQuery<Activity[]>({
    queryKey: ['lead-activities', leadId],
    queryFn: () => fetcher<Activity[]>(`/api/v2/crm/leads/${leadId}/activities`),
    enabled: open && tab === 'activities',
  });

  const { register, handleSubmit } = useForm<Partial<Lead>>({
    values: lead ?? undefined,
  });

  const save = useMutation({
    mutationFn: (data: Partial<Lead>) =>
      fetcher(`/api/v2/crm/leads/${leadId}`, { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lead', leadId] });
      qc.invalidateQueries({ queryKey: ['leads', clinicId] });
    },
  });

  const convert = useMutation({
    mutationFn: () =>
      fetcher<{ patient_id: string }>(`/api/v2/crm/leads/${leadId}/convert`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['leads', clinicId] });
      onClose();
    },
  });

  const title = lead ? `${lead.first_name} ${lead.last_name}` : 'Lead';

  return (
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <SheetContent side="right" className="w-full max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
        </SheetHeader>

        {/* Tab bar — uses Button so role="button" is preserved for tests */}
        <div className="mb-4 mt-4 flex gap-2 border-b border-zinc-200">
          {TABS.map((t) => (
            <Button
              key={t}
              variant="ghost"
              size="sm"
              onClick={() => setTab(t)}
              className={`capitalize ${tab === t ? 'border-b-2 border-blue-600 font-medium text-blue-600 rounded-none' : 'text-zinc-500'}`}
            >
              {t}
            </Button>
          ))}
        </div>

        {tab === 'detail' && lead && (
          <form onSubmit={handleSubmit((d) => save.mutate(d))} className="flex flex-col gap-3">
            <input {...register('first_name')} aria-label="first_name" placeholder="First name" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
            <input {...register('last_name')} aria-label="last_name" placeholder="Last name" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
            <input {...register('phone')} aria-label="phone" placeholder="Phone" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
            <input {...register('email')} aria-label="email" placeholder="Email" type="email" className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
            <select {...register('owner_id')} aria-label="owner_id" className="rounded border border-zinc-300 px-3 py-1.5 text-sm">
              <option value="">No owner</option>
              {providers.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <select {...register('status')} aria-label="status" className="rounded border border-zinc-300 px-3 py-1.5 text-sm">
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <textarea {...register('notes')} aria-label="notes" placeholder="Notes" rows={3} className="rounded border border-zinc-300 px-3 py-1.5 text-sm" />
            <Button type="submit" disabled={save.isPending}>Save</Button>
          </form>
        )}

        {tab === 'activities' && (
          <div>
            <AddActivityForm leadId={leadId} />
            <LeadActivityTimeline activities={activities} />
          </div>
        )}

        {tab === 'convert' && (
          <div className="flex flex-col gap-3 pt-4">
            <p className="text-sm text-zinc-600">
              Convert this lead into a patient record.
            </p>
            <Button
              onClick={() => convert.mutate()}
              disabled={convert.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              Convert to patient
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
