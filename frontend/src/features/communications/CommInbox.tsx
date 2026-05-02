import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';

type Channel = 'sms' | 'email' | 'whatsapp';

interface Message {
  id: string;
  patient_id: string;
  channel: Channel;
  direction: 'inbound' | 'outbound';
  body: string;
  status: string;
  created_at: string;
  patient_name?: string;
  from?: string;
}

interface Thread {
  patient_id: string;
  patient_name: string;
  messages: Message[];
  last_at: string;
}

const CHANNEL_ICONS: Record<Channel, string> = {
  sms: '📱',
  email: '✉️',
  whatsapp: '💬',
};

function groupByPatient(msgs: Message[]): Thread[] {
  const map = new Map<string, Thread>();
  for (const m of msgs) {
    if (!map.has(m.patient_id)) {
      map.set(m.patient_id, {
        patient_id: m.patient_id,
        patient_name: m.patient_name ?? m.patient_id,
        messages: [],
        last_at: m.created_at,
      });
    }
    const t = map.get(m.patient_id)!;
    t.messages.push(m);
    if (m.created_at > t.last_at) t.last_at = m.created_at;
  }
  return Array.from(map.values()).sort((a, b) => b.last_at.localeCompare(a.last_at));
}

interface ComposeState {
  channel: Channel;
  to: string;
}

interface ComposeProps {
  initial?: Partial<ComposeState>;
  onClose: () => void;
}

function ComposeDialog({ initial, onClose }: ComposeProps) {
  const qc = useQueryClient();
  const clinicId = useAuthStore((s) => s.clinicId);
  const [patientId, setPatientId] = useState('');
  const [channel, setChannel] = useState<Channel>(initial?.channel ?? 'sms');
  const [to, setTo] = useState(initial?.to ?? '');
  const [body, setBody] = useState('');

  const send = useMutation({
    mutationFn: () =>
      fetcher('/api/v2/communications/send', {
        method: 'POST',
        body: JSON.stringify({ patient_id: patientId, channel, body, to }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['communications', clinicId] });
      onClose();
    },
  });

  const channels: Channel[] = ['sms', 'email', 'whatsapp'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-96 rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 font-semibold">New Message</h3>
        <div className="space-y-3 text-sm">
          <div>
            <label className="block text-zinc-600">Patient ID</label>
            <input
              required
              className="mt-1 w-full rounded border px-2 py-1"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">To</label>
            <input
              className="mt-1 w-full rounded border px-2 py-1"
              value={to}
              onChange={(e) => setTo(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-zinc-600">Channel</label>
            <div className="mt-1 flex gap-1">
              {channels.map((ch) => (
                <button
                  key={ch}
                  type="button"
                  aria-pressed={channel === ch}
                  onClick={() => setChannel(ch)}
                  className={`flex-1 rounded border px-2 py-1 capitalize ${
                    channel === ch
                      ? 'border-blue-600 bg-blue-600 text-white'
                      : 'border-zinc-300 hover:bg-zinc-50'
                  }`}
                >
                  {ch}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-zinc-600">Message</label>
            <textarea
              rows={4}
              className="mt-1 w-full rounded border px-2 py-1"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </div>
          {send.error && (
            <p className="text-xs text-red-600">{(send.error as Error).message}</p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button className="rounded px-3 py-1 hover:bg-zinc-100" onClick={onClose}>
              Cancel
            </button>
            <button
              disabled={send.isPending || !patientId || !body}
              onClick={() => send.mutate()}
              className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {send.isPending ? 'Sending…' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CommInbox() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const [selected, setSelected] = useState<string | null>(null);
  const [compose, setCompose] = useState<Partial<ComposeState> | null>(null);

  const { data: messages = [], isLoading } = useQuery<Message[]>({
    queryKey: ['communications', clinicId],
    queryFn: () => fetcher<Message[]>('/api/v2/communications'),
  });

  const threads = groupByPatient(messages);
  const activeThread = threads.find((t) => t.patient_id === selected);

  return (
    <div className="flex h-[600px] gap-0 overflow-hidden rounded border border-zinc-200">
      {/* Thread list */}
      <div className="flex w-64 shrink-0 flex-col border-r border-zinc-200">
        <div className="flex items-center justify-between border-b border-zinc-200 p-3">
          <span className="text-sm font-medium">Inbox</span>
          <button
            className="rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-700"
            onClick={() => setCompose({})}
          >
            Compose
          </button>
        </div>
        {isLoading ? (
          <p className="p-3 text-xs text-zinc-400">Loading…</p>
        ) : (
          <ul className="flex-1 overflow-y-auto">
            {threads.map((t) => (
              <li
                key={t.patient_id}
                className={`cursor-pointer border-b border-zinc-100 p-3 hover:bg-zinc-50 ${
                  selected === t.patient_id ? 'bg-blue-50' : ''
                }`}
                onClick={() => setSelected(t.patient_id)}
              >
                <div className="text-sm font-medium">{t.patient_name}</div>
                <div className="truncate text-xs text-zinc-500">
                  {t.messages[t.messages.length - 1]?.body}
                </div>
              </li>
            ))}
            {threads.length === 0 && (
              <li className="p-3 text-xs text-zinc-400">No messages</li>
            )}
          </ul>
        )}
      </div>

      {/* Message thread */}
      <div className="flex flex-1 flex-col">
        {activeThread ? (
          <>
            <div className="border-b border-zinc-200 p-3 text-sm font-medium">
              {activeThread.patient_name}
            </div>
            <ul className="flex-1 space-y-2 overflow-y-auto p-4">
              {activeThread.messages.map((m) => (
                <li
                  key={m.id}
                  className={`flex ${m.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs rounded-lg px-3 py-2 text-sm ${
                      m.direction === 'outbound'
                        ? 'bg-blue-600 text-white'
                        : 'bg-zinc-100 text-zinc-800'
                    }`}
                  >
                    <div>{m.body}</div>
                    <div className="mt-0.5 text-xs opacity-60">
                      {CHANNEL_ICONS[m.channel]} {m.channel} · {new Date(m.created_at).toLocaleTimeString('en-CA')}
                    </div>
                    {m.direction === 'inbound' && (
                      <button
                        className="mt-1 text-xs underline opacity-70 hover:opacity-100"
                        onClick={() => setCompose({ channel: m.channel, to: m.from })}
                      >
                        Reply
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center text-sm text-zinc-400">
            Select a conversation
          </div>
        )}
      </div>

      {compose !== null && (
        <ComposeDialog initial={compose} onClose={() => setCompose(null)} />
      )}
    </div>
  );
}
