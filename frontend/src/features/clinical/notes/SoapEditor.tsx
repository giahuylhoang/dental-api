import { useState, useEffect } from 'react';

export interface SoapNote {
  id?: string;
  patient_id: string;
  soap_subjective: string;
  soap_objective: string;
  soap_assessment: string;
  soap_plan: string;
  locked_at?: string | null;
  supersedes_id?: string | null;
}

interface SoapEditorProps {
  patientId: string;
  initialNote?: SoapNote;
  onSave?: (note: SoapNote) => void;
}

export default function SoapEditor({ patientId, initialNote, onSave }: SoapEditorProps) {
  const [note, setNote] = useState<SoapNote>(
    initialNote ?? {
      patient_id: patientId,
      soap_subjective: '',
      soap_objective: '',
      soap_assessment: '',
      soap_plan: '',
      locked_at: null,
    },
  );
  const [isAmending, setIsAmending] = useState(false);
  const [amendNote, setAmendNote] = useState<SoapNote | null>(null);
  const [confirmLock, setConfirmLock] = useState(false);

  const isLocked = !!note.locked_at;
  const activeNote = isAmending && amendNote ? amendNote : note;
  const setActiveNote = isAmending && amendNote
    ? (updater: (prev: SoapNote) => SoapNote) => setAmendNote((prev) => updater(prev!))
    : (updater: (prev: SoapNote) => SoapNote) => setNote(updater);

  // Autosave draft every 5s
  useEffect(() => {
    if (isLocked && !isAmending) return;
    const timer = setTimeout(() => {
      onSave?.(activeNote);
    }, 5000);
    return () => clearTimeout(timer);
  }, [activeNote, isLocked, isAmending, onSave]);

  function handleLock() {
    if (!confirmLock) {
      setConfirmLock(true);
      return;
    }
    setNote((prev) => ({ ...prev, locked_at: new Date().toISOString() }));
    setConfirmLock(false);
    onSave?.({ ...note, locked_at: new Date().toISOString() });
  }

  function handleAmend() {
    setAmendNote({
      patient_id: patientId,
      soap_subjective: '',
      soap_objective: '',
      soap_assessment: '',
      soap_plan: '',
      locked_at: null,
      supersedes_id: note.id,
    });
    setIsAmending(true);
  }

  const fields: Array<{ key: keyof SoapNote; label: string; fieldId: string }> = [
    { key: 'soap_subjective', label: 'Subjective', fieldId: 'soap-subjective' },
    { key: 'soap_objective', label: 'Objective', fieldId: 'soap-objective' },
    { key: 'soap_assessment', label: 'Assessment', fieldId: 'soap-assessment' },
    { key: 'soap_plan', label: 'Plan', fieldId: 'soap-plan' },
  ];

  const displayNote = isAmending && amendNote ? amendNote : note;
  const disabled = isLocked && !isAmending;

  return (
    <div className="space-y-4">
      {isAmending && (
        <div className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-700">
          Amending note — this will create a new note superseding #{note.id}.
        </div>
      )}
      {isLocked && !isAmending && (
        <div className="rounded bg-zinc-100 px-3 py-2 text-sm text-zinc-600">
          This note is locked. Use Amend to add a correction.
        </div>
      )}
      {fields.map(({ key, label, fieldId }) => (
        <div key={key}>
          <label htmlFor={fieldId} className="mb-1 block text-sm font-medium text-zinc-700">{label}</label>
          <textarea
            id={fieldId}
            value={String(displayNote[key] ?? '')}
            disabled={disabled}
            onChange={(e) =>
              setActiveNote((prev) => ({ ...prev, [key]: e.target.value }))
            }
            rows={3}
            className="w-full rounded border border-zinc-300 px-3 py-2 text-sm disabled:bg-zinc-50 disabled:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </div>
      ))}
      <div className="flex gap-2">
        {!isLocked && (
          <>
            <button
              onClick={() => onSave?.(note)}
              className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700"
            >
              Save Draft
            </button>
            <button
              onClick={handleLock}
              className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
            >
              {confirmLock ? 'Confirm Lock?' : 'Lock'}
            </button>
          </>
        )}
        {isLocked && !isAmending && (
          <button
            onClick={handleAmend}
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
          >
            Amend
          </button>
        )}
        {isAmending && (
          <>
            <button
              onClick={() => onSave?.(amendNote!)}
              className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700"
            >
              Save Amendment
            </button>
            <button
              onClick={() => { setIsAmending(false); setAmendNote(null); }}
              className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
            >
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  );
}
