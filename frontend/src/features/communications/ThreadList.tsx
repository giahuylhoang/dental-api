import type { Thread, Channel } from './types';

const CHANNEL_ICONS: Record<Channel, string> = { sms: '📱', email: '✉️', whatsapp: '💬' };

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

export function ThreadList({ threads, selected, onSelect }: Props) {
  return (
    <ul className="flex-1 overflow-y-auto">
      {threads.map((t) => {
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
      {threads.length === 0 && (
        <li className="p-3 text-xs text-zinc-400">No messages</li>
      )}
    </ul>
  );
}
