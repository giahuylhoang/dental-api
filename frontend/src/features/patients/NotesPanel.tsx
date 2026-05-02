import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import SoapEditor, { type SoapNote } from '../clinical/notes/SoapEditor';

// Extends SoapNote with server-side fields
interface StoredNote extends SoapNote {
  created_at?: string;
  updated_at?: string;
}

interface NotesPanelProps {
  patientId: string;
}

export default function NotesPanel({ patientId }: NotesPanelProps) {
  const qc = useQueryClient();
  const [activeNote, setActiveNote] = useState<StoredNote | null>(null);

  const { data: notes = [], isLoading } = useQuery<StoredNote[]>({
    queryKey: ['clinical-notes', patientId],
    queryFn: () => fetcher<StoredNote[]>(`/api/v2/clinical/notes?patient_id=${patientId}`),
  });

  const saveMutation = useMutation({
    mutationFn: (note: SoapNote) => {
      if (note.id) {
        return fetcher<StoredNote>(`/api/v2/clinical/notes/${note.id}`, {
          method: 'PATCH',
          body: JSON.stringify(note),
        });
      }
      return fetcher<StoredNote>(`/api/v2/clinical/notes`, {
        method: 'POST',
        body: JSON.stringify(note),
      });
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['clinical-notes', patientId] });
      setActiveNote(null);
    },
  });

  const lockMutation = useMutation({
    mutationFn: (noteId: string) =>
      fetcher<StoredNote>(`/api/v2/clinical/notes/${noteId}/lock`, { method: 'POST' }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['clinical-notes', patientId] });
    },
  });

  function openNew() {
    setActiveNote({
      patient_id: patientId,
      soap_subjective: '',
      soap_objective: '',
      soap_assessment: '',
      soap_plan: '',
      locked_at: null,
    });
  }

  if (activeNote) {
    return (
      <div className="space-y-3">
        <button
          onClick={() => setActiveNote(null)}
          className="text-sm text-zinc-500 hover:text-zinc-700"
        >
          ← Back to notes
        </button>
        <SoapEditor
          patientId={patientId}
          initialNote={activeNote}
          onSave={(note) => saveMutation.mutate(note)}
        />
      </div>
    );
  }

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  const sorted = [...notes].sort((a, b) => {
    const ta = a.created_at ?? '';
    const tb = b.created_at ?? '';
    return tb.localeCompare(ta);
  });

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <button
          onClick={openNew}
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700"
        >
          New note
        </button>
      </div>

      {sorted.length === 0 && <p className="text-sm text-zinc-500">No notes yet.</p>}

      {sorted.map((note) => {
        const locked = !!note.locked_at;
        return (
          <div
            key={note.id}
            className="flex items-start justify-between rounded border border-zinc-200 px-3 py-2 text-sm"
          >
            <button
              className="flex-1 text-left hover:underline"
              onClick={() => setActiveNote(note)}
            >
              <span className="font-medium">
                {locked ? '🔒 ' : ''}
                {note.created_at ? new Date(note.created_at).toLocaleString() : 'Note'}
              </span>
              <p className="mt-0.5 line-clamp-1 text-zinc-500">
                {note.soap_subjective || note.soap_objective || '(empty)'}
              </p>
            </button>
            {!locked && note.id && (
              <button
                onClick={() => lockMutation.mutate(note.id!)}
                disabled={lockMutation.isPending}
                className="ml-2 rounded border border-zinc-200 px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
              >
                Lock
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
