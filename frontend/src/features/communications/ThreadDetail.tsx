import type { Thread, Message } from './types';
import { MessageBubble } from './MessageBubble';
import { Button } from '../../components/ui/button';

interface Props {
  thread: Thread | null;
  onReply: (msg: Message) => void;
}

export function ThreadDetail({ thread, onReply }: Props) {
  if (!thread) {
    return (
      <div className="flex flex-1 h-full items-center justify-center text-sm text-zinc-400">
        Select a conversation
      </div>
    );
  }

  const lastMsg = thread.messages[thread.messages.length - 1];

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-zinc-200 p-3 text-sm font-medium">
        {thread.patient_name}
        <span className="ml-2 text-xs text-zinc-400">{thread.channel}</span>
      </div>
      <ul className="flex-1 space-y-2 overflow-y-auto p-4">
        {thread.messages.map((m) => (
          <MessageBubble key={m.id} message={m} onReply={onReply} />
        ))}
      </ul>
      {lastMsg && (
        <div className="border-t border-zinc-200 p-3">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onReply(lastMsg)}
          >
            Reply
          </Button>
        </div>
      )}
    </div>
  );
}
