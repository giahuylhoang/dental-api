import { useState } from 'react';
import type { Thread, Channel } from './types';

const CHANNEL_ICONS: Record<Channel, string> = { sms: '📱', email: '✉️', whatsapp: '💬' };

const FILTERS: Array<{ label: string; value: Channel | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'SMS', value: 'sms' },
  { label: 'Email', value: 'email' },
  { label: 'WhatsApp', value: 'whatsapp' },
];

function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

interface Props {
  threads: Thread[];
  selected: string | null;
  onSelect: (threadKey: string) => void;
  onCompose: () => void;
}

export function ThreadList({ threads, selected, onSelect, onCompose }: Props) {
  const [filter, setFilter] = useState<Channel | 'all'>('all');

  const visible = filter === 'all' ? threads : threads.filter((t) => t.channel === filter);

  return (
    <div className="flex w-64 shrink-0 flex-col border-r border-zinc-200">
      <div className="flex items-center justify-between border-b border-zinc-200 p-3">
        <span className="text-sm font-medium">Inbox</span>
        <button
          className="rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-700"
          onClick={onCompose}
        >
          + Compose
        </button>
      </div>

      {/* Channel filter chips */}
      <div className="flex gap-1 border-b border-zinc-100 p-2" role="tablist" aria-label="Channel filter">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            role="tab"
            aria-selected={filter === f.value}
            onClick={() => setFilter(f.value)}
            className={`rounded-full px-2 py-0.5 text-xs ${
              filter === f.value ? 'bg-blue-600 text-white' : 'bg-zinc-100 hover:bg-zinc-200'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <ul className="flex-1 overflow-y-auto">
        {visible.map((t) => {
          const unread = t.messages.filter((m) => m.direction === 'inbound' && !m.read_at).length;
          const last = t.messages[t.messages.length - 1];
          return (
            <li
              key={t.thread_key}
              data-testid="thread-row"
              className={`cursor-pointer border-b border-zinc-100 p-3 hover:bg-zinc-50 ${
                selected === t.thread_key ? 'bg-blue-50' : ''
              }`}
              onClick={() => onSelect(t.thread_key)}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{t.patient_name}</span>
                <span className="text-xs text-zinc-400">{relativeTime(t.last_at)}</span>
              </div>
              <div className="flex items-center gap-1">
                <span>{CHANNEL_ICONS[t.channel]}</span>
                <span className="truncate text-xs text-zinc-500 max-w-[140px]">
                  {last?.body.slice(0, 60)}
                </span>
                {unread > 0 && (
                  <span className="ml-auto rounded-full bg-blue-600 px-1.5 text-xs text-white">
                    {unread}
                  </span>
                )}
              </div>
            </li>
          );
        })}
        {visible.length === 0 && (
          <li className="p-3 text-xs text-zinc-400">No messages</li>
        )}
      </ul>
    </div>
  );
}
