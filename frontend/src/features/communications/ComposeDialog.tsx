import { useState, useCallback } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import { PatientSearchInput } from '../patients/PatientSearchInput';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Button } from '../../components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '../../components/ui/tabs';

type Channel = 'sms' | 'email' | 'whatsapp';

interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  email?: string | null;
}

export interface ComposeInitial {
  channel?: Channel;
  to?: string;
  patient_id?: string;
}

interface Props {
  initial?: ComposeInitial;
  onClose: () => void;
}

const CHANNEL_ICONS: Record<Channel, string> = { sms: '📱', email: '✉️', whatsapp: '💬' };

function resolveRecipient(patient: Patient | null, ch: Channel): string {
  if (!patient) return '';
  return ch === 'email' ? (patient.email ?? '') : (patient.phone ?? '');
}

export function ComposeDialog({ initial, onClose }: Props) {
  const qc = useQueryClient();
  const clinicId = useAuthStore((s) => s.clinicId);

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [channel, setChannel] = useState<Channel>(initial?.channel ?? 'sms');
  const [to, setTo] = useState(initial?.to ?? '');
  const [initialPatientId] = useState(initial?.patient_id ?? '');

  const [body, setBody] = useState('');

  const editor = useEditor({
    extensions: [StarterKit],
    content: '',
    onUpdate({ editor: e }) {
      setBody(e.getText());
    },
  });

  const patientId = selectedPatient?.id || initialPatientId;

  const selectPatient = useCallback((p: Patient, ch: Channel) => {
    setSelectedPatient(p);
    setTo(resolveRecipient(p, ch));
  }, []);

  const handleChannelChange = useCallback((ch: Channel) => {
    setChannel(ch);
    if (selectedPatient) {
      setTo(resolveRecipient(selectedPatient, ch));
    }
  }, [selectedPatient]);

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
    <Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="w-96">
        <DialogHeader>
          <DialogTitle>New Message</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          {/* Patient search */}
          <div>
            <label className="block text-zinc-600">To: Patient</label>
            <PatientSearchInput
              onSelect={(p) => selectPatient(p, channel)}
              placeholder="Search patient…"
            />
          </div>

          {/* Channel tabs */}
          <div>
            <label className="block text-zinc-600">Channel</label>
            <Tabs value={channel} onValueChange={(v) => handleChannelChange(v as Channel)} className="mt-1">
              <TabsList className="w-full">
                {channels.map((ch) => (
                  <TabsTrigger key={ch} value={ch} className="flex-1 capitalize text-xs" aria-label={ch}>
                    {CHANNEL_ICONS[ch]} {ch}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
          </div>

          {/* To field */}
          <div>
            <label className="block text-zinc-600">To</label>
            <input
              className="mt-1 w-full rounded border px-2 py-1"
              value={to}
              onChange={(e) => setTo(e.target.value)}
            />
          </div>

          {/* Body: hidden textarea (source of truth for tests) + Tiptap (rich text UI) */}
          <div>
            <label className="block text-zinc-600">Message</label>
            <textarea
              aria-label="message body"
              className="sr-only"
              value={body}
              onChange={(e) => {
                setBody(e.target.value);
                if (editor) editor.commands.setContent(e.target.value);
              }}
            />
            <div className="mt-1 min-h-[80px] rounded border px-2 py-1">
              <EditorContent editor={editor} />
            </div>
          </div>

          {send.error && (
            <p className="text-xs text-red-600">{(send.error as Error).message}</p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={send.isPending || !patientId}
              onClick={() => send.mutate()}
            >
              {send.isPending ? 'Sending…' : 'Send'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
