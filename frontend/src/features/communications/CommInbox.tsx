import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import { ThreadList } from './ThreadList';
import { ThreadDetail } from './ThreadDetail';
import { ComposeDialog } from './ComposeDialog';
import type { Message, Thread, Channel } from './types';

function groupByThread(msgs: Message[]): Thread[] {
  const map = new Map<string, Thread>();
  for (const m of msgs) {
    const key = m.thread_key ?? `${m.patient_id}:${m.channel}`;
    if (!map.has(key)) {
      map.set(key, {
        thread_key: key,
        patient_id: m.patient_id,
        patient_name: m.patient_name ?? m.patient_id,
        channel: m.channel,
        messages: [],
        last_at: m.created_at,
      });
    }
    const t = map.get(key)!;
    t.messages.push(m);
    if (m.created_at > t.last_at) t.last_at = m.created_at;
  }
  return Array.from(map.values()).sort((a, b) => b.last_at.localeCompare(a.last_at));
}

interface ComposeState {
  channel?: Channel;
  to?: string;
  patient_id?: string;
}

export default function CommInbox() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [compose, setCompose] = useState<ComposeState | null>(null);

  const { data: messages = [], isLoading } = useQuery<Message[]>({
    queryKey: ['communications', clinicId],
    queryFn: () => fetcher<Message[]>('/api/v2/communications'),
  });

  const threads = groupByThread(messages);
  const activeThread = threads.find((t) => t.thread_key === selected) ?? null;

  function handleSelect(threadKey: string) {
    setSelected(threadKey);
    // Mark thread read — fire and forget
    fetcher(`/api/v2/communications/threads/${threadKey}/read`, { method: 'PATCH' })
      .then(() => qc.invalidateQueries({ queryKey: ['communications', clinicId] }))
      .catch((e) => console.warn('mark-read failed', e));
  }

  return (
    <div className="flex h-[600px] gap-0 overflow-hidden rounded border border-zinc-200">
      {isLoading ? (
        <p className="p-3 text-xs text-zinc-400">Loading…</p>
      ) : (
        <ThreadList
          threads={threads}
          selected={selected}
          onSelect={handleSelect}
          onCompose={() => setCompose({})}
        />
      )}

      <ThreadDetail
        thread={activeThread}
        onReply={(msg) =>
          setCompose({ channel: msg.channel, to: msg.from, patient_id: msg.patient_id })
        }
      />

      {compose !== null && (
        <ComposeDialog initial={compose} onClose={() => setCompose(null)} />
      )}
    </div>
  );
}
