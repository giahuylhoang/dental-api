import type { Thread, Message } from './types';
import { MessageBubble } from './MessageBubble';

interface Props {
  thread: Thread | null;
  onReply: (msg: Message) => void;
}

export function ThreadDetail({ thread, onReply }: Props) {
  if (!thread) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-zinc-400">
        Select a conversation
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-zinc-200 p-3 text-sm font-medium">
        {thread.patient_name}
      </div>
      <ul className="flex-1 space-y-2 overflow-y-auto p-4">
        {thread.messages.map((m) => (
          <MessageBubble key={m.id} message={m} onReply={onReply} />
        ))}
      </ul>
    </div>
  );
}
