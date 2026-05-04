"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetcher } from "@/lib/api/client";

interface Note {
  id?: string;
  patient_id: string;
  soap_subjective: string;
  soap_objective: string;
  soap_assessment: string;
  soap_plan: string;
  locked_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export function NotesPanel({ patientId }: { patientId: string }) {
  const qc = useQueryClient();
  const [activeNote, setActiveNote] = useState<Note | null>(null);

  const { data: notes = [], isLoading } = useQuery<Note[]>({
    queryKey: ["clinical-notes", patientId],
    queryFn: () => fetcher<Note[]>(`/api/v2/clinical/notes?patient_id=${patientId}`),
  });

  const saveMutation = useMutation({
    mutationFn: (note: Note) => {
      if (note.id) {
        return fetcher<Note>(`/api/v2/clinical/notes/${note.id}`, { method: "PATCH", body: JSON.stringify(note) });
      }
      return fetcher<Note>(`/api/v2/clinical/notes`, { method: "POST", body: JSON.stringify(note) });
    },
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ["clinical-notes", patientId] }); setActiveNote(null); },
  });

  const lockMutation = useMutation({
    mutationFn: (noteId: string) => fetcher<Note>(`/api/v2/clinical/notes/${noteId}/lock`, { method: "POST" }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["clinical-notes", patientId] }),
  });

  if (activeNote) {
    return (
      <div className="space-y-3">
        <button onClick={() => setActiveNote(null)} className="text-sm text-muted-foreground hover:text-foreground">← Back to notes</button>
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(activeNote); }} className="space-y-3">
          {(["soap_subjective", "soap_objective", "soap_assessment", "soap_plan"] as const).map((field) => (
            <div key={field}>
              <label className="block text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1">{field.replace("soap_", "")}</label>
              <textarea
                rows={3}
                value={activeNote[field]}
                onChange={(e) => setActiveNote((n) => n ? { ...n, [field]: e.target.value } : n)}
                className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
              />
            </div>
          ))}
          <div className="flex gap-2">
            <button type="submit" disabled={saveMutation.isPending} className="rounded bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-80 disabled:opacity-50">Save</button>
            <button type="button" onClick={() => setActiveNote(null)} className="rounded border border-border px-3 py-1.5 text-sm hover:bg-muted">Cancel</button>
          </div>
        </form>
      </div>
    );
  }

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;

  const sorted = [...notes].sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""));

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <button
          onClick={() => setActiveNote({ patient_id: patientId, soap_subjective: "", soap_objective: "", soap_assessment: "", soap_plan: "", locked_at: null })}
          className="rounded bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-80"
        >
          New note
        </button>
      </div>
      {sorted.length === 0 && <p className="text-sm text-muted-foreground">No notes yet.</p>}
      {sorted.map((note) => {
        const locked = !!note.locked_at;
        return (
          <div key={note.id} className="flex items-start justify-between rounded border border-border px-3 py-2 text-sm">
            <button className="flex-1 text-left hover:underline" onClick={() => setActiveNote(note)}>
              <span className="font-medium">{locked ? "🔒 " : ""}{note.created_at ? new Date(note.created_at).toLocaleString() : "Note"}</span>
              <p className="mt-0.5 line-clamp-1 text-muted-foreground">{note.soap_subjective || note.soap_objective || "(empty)"}</p>
            </button>
            {!locked && note.id && (
              <button onClick={() => lockMutation.mutate(note.id!)} disabled={lockMutation.isPending} className="ml-2 rounded border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-muted">
                Lock
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
