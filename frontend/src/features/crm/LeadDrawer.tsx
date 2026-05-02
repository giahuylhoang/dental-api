import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import Drawer from '../../components/Drawer';
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

type Tab = 'detail' | 'activities';

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
    <Drawer open={open} onClose={onClose} title={title} width="lg">
      {/* Tabs */}
      <div className="mb-4 flex gap-2 border-b border-zinc-200">
        {(['detail', 'activities'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 text-sm capitalize ${tab === t ? 'border-b-2 border-blue-600 font-medium text-blue-600' : 'text-zinc-500 hover:text-zinc-800'}`}
          >
            {t}
          </button>
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
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={() => convert.mutate()}
              disabled={convert.isPending}
              className="rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
            >
              Convert to patient
            </button>
            <button type="submit" disabled={save.isPending} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
              Save
            </button>
          </div>
        </form>
      )}

      {tab === 'activities' && (
        <div>
          <AddActivityForm leadId={leadId} />
          <LeadActivityTimeline activities={activities} />
        </div>
      )}
    </Drawer>
  );
}
