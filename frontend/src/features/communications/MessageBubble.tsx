import type { Message, Channel } from './types';

const CHANNEL_ICONS: Record<Channel, string> = { sms: '📱', email: '✉️', whatsapp: '💬' };

interface Props {
  message: Message;
  onReply?: (msg: Message) => void;
}

export function MessageBubble({ message: m }: Props) {
  const isOut = m.direction === 'outbound';
  return (
    <li className={`flex ${isOut ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs px-3 py-2 text-sm ${
          isOut
            ? 'rounded-2xl rounded-br-sm bg-primary text-primary-foreground'
            : 'rounded-2xl rounded-bl-sm bg-muted text-foreground'
        }`}
      >
        <div>{m.body}</div>
        <div className="mt-0.5 text-xs opacity-60">
          {CHANNEL_ICONS[m.channel]} {new Date(m.created_at).toLocaleTimeString('en-CA')}
          {m.status && ` · ${m.status}`}
        </div>
      </div>
    </li>
  );
}
