import type { Message, Channel } from './types';

const CHANNEL_ICONS: Record<Channel, string> = { sms: '📱', email: '✉️', whatsapp: '💬' };

interface Props {
  message: Message;
  onReply?: (msg: Message) => void;
}

export function MessageBubble({ message: m, onReply }: Props) {
  const isOut = m.direction === 'outbound';
  return (
    <li className={`flex ${isOut ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs rounded-lg px-3 py-2 text-sm ${
          isOut ? 'bg-zinc-900 text-white' : 'bg-zinc-200 text-zinc-800'
        }`}
      >
        <div>{m.body}</div>
        <div className="mt-0.5 text-xs opacity-60">
          {CHANNEL_ICONS[m.channel]} {new Date(m.created_at).toLocaleTimeString('en-CA')}
          {m.status && ` · ${m.status}`}
        </div>
        {!isOut && onReply && (
          <button
            className="mt-1 text-xs underline opacity-70 hover:opacity-100"
            onClick={() => onReply(m)}
          >
            Reply
          </button>
        )}
      </div>
    </li>
  );
}
