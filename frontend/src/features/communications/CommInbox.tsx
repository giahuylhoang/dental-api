import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Group as PanelGroup, Panel, Separator as PanelResizeHandle } from 'react-resizable-panels';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
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

const CHANNELS: Array<{ label: string; value: Channel | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'SMS', value: 'sms' },
  { label: 'Email', value: 'email' },
  { label: 'WhatsApp', value: 'whatsapp' },
];

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
  const [channelFilter, setChannelFilter] = useState<Channel | 'all'>('all');

  const { data: messages = [], isLoading } = useQuery<Message[]>({
    queryKey: ['communications', clinicId],
    queryFn: () => fetcher<Message[]>('/api/v2/communications'),
  });

  const threads = groupByThread(messages);
  const filteredThreads = channelFilter === 'all' ? threads : threads.filter((t) => t.channel === channelFilter);
  const activeThread = threads.find((t) => t.thread_key === selected) ?? null;

  function handleSelect(threadKey: string) {
    setSelected(threadKey);
    fetcher(`/api/v2/communications/threads/${threadKey}/read`, { method: 'PATCH' })
      .then(() => qc.invalidateQueries({ queryKey: ['communications', clinicId] }))
      .catch((e) => console.warn('mark-read failed', e));
  }

  return (
    <div className="h-[600px] overflow-hidden rounded border border-zinc-200">
      {isLoading ? (
        <p className="p-3 text-xs text-zinc-400">Loading…</p>
      ) : (
        <PanelGroup orientation="horizontal">
          <Panel defaultSize={30} minSize={20}>
            <div className="flex h-full flex-col border-r border-zinc-200">
              {/* Header: channel filter chips + compose button */}
              <div className="flex flex-wrap items-center gap-1 border-b border-zinc-200 p-2">
                {CHANNELS.map((ch) => (
                  <Badge
                    key={ch.value}
                    variant={channelFilter === ch.value ? 'default' : 'outline'}
                    className="cursor-pointer select-none"
                    onClick={() => setChannelFilter(ch.value)}
                  >
                    {ch.label}
                  </Badge>
                ))}
                <Button
                  size="sm"
                  className="ml-auto"
                  onClick={() => setCompose({})}
                >
                  + Compose
                </Button>
              </div>
              <ThreadList
                threads={filteredThreads}
                selected={selected}
                onSelect={handleSelect}
                onCompose={() => setCompose({})}
              />
            </div>
          </Panel>
          <PanelResizeHandle className="w-1 bg-zinc-200 hover:bg-zinc-300 cursor-col-resize" />
          <Panel defaultSize={70} minSize={30}>
            <ThreadDetail
              thread={activeThread}
              onReply={(msg) =>
                setCompose({ channel: msg.channel, to: msg.from, patient_id: msg.patient_id })
              }
            />
          </Panel>
        </PanelGroup>
      )}

      {compose !== null && (
        <ComposeDialog initial={compose} onClose={() => setCompose(null)} />
      )}
    </div>
  );
}
