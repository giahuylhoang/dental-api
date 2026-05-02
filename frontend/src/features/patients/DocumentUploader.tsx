import { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../features/auth/store';
import type { components } from '../../api/v2/types';

type DocumentUpload = components['schemas']['DocumentUpload'];
type DocKind = 'photo' | 'xray' | 'consent' | 'other';

interface DocumentUploaderProps {
  patientId: string;
}

export default function DocumentUploader({ patientId }: DocumentUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState<DocKind>('other');
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  const { accessToken, clinicId } = useAuthStore();

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected');
      const fd = new FormData();
      fd.append('file', file);
      fd.append('kind', kind);
      fd.append('patient_id', patientId);
      const headers: Record<string, string> = { 'X-Clinic-Id': clinicId };
      if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
      const res = await fetch('/api/v2/clinical/documents/upload', {
        method: 'POST',
        headers,
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error((err as { detail: string }).detail ?? res.statusText);
      }
      return res.json() as Promise<DocumentUpload>;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['documents', patientId] });
      setFile(null);
    },
  });

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    if (picked) setFile(picked);
  }

  const isImage = file && file.type.startsWith('image/');

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed px-4 py-8 text-sm transition-colors ${dragging ? 'border-zinc-500 bg-zinc-50' : 'border-zinc-300 hover:border-zinc-400'}`}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          data-testid="file-input"
        />
        {file ? (
          <div className="flex flex-col items-center gap-2">
            {isImage && (
              <img
                src={URL.createObjectURL(file)}
                alt="preview"
                className="h-24 w-24 rounded object-cover"
              />
            )}
            <span className="font-medium">{file.name}</span>
            <span className="text-zinc-500">{(file.size / 1024).toFixed(1)} KB</span>
          </div>
        ) : (
          <span className="text-zinc-500">Drag & drop or click to choose file</span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <label htmlFor="doc-kind" className="text-sm text-zinc-700">Kind:</label>
        <select
          id="doc-kind"
          value={kind}
          onChange={(e) => setKind(e.target.value as DocKind)}
          className="rounded border border-zinc-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
        >
          <option value="photo">Photo</option>
          <option value="xray">X-Ray</option>
          <option value="consent">Consent</option>
          <option value="other">Other</option>
        </select>
      </div>

      {uploadMutation.isError && (
        <p className="text-sm text-red-600">{(uploadMutation.error as Error).message}</p>
      )}
      {uploadMutation.isSuccess && (
        <p className="text-sm text-green-600">Uploaded successfully.</p>
      )}

      <button
        onClick={() => uploadMutation.mutate()}
        disabled={!file || uploadMutation.isPending}
        className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-50"
      >
        {uploadMutation.isPending ? 'Uploading…' : 'Upload'}
      </button>
    </div>
  );
}
