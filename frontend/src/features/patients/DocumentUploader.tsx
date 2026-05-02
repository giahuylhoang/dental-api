import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../features/auth/store';

type DocKind = 'photo' | 'xray' | 'consent' | 'insurance' | 'other';

interface QueueItem {
  id: string;
  file: File;
  kind: DocKind;
  progress: number;
  status: 'pending' | 'uploading' | 'done' | 'error';
  error?: string;
}

interface DocumentUploaderProps {
  patientId: string;
  defaultKind?: DocKind;
}

function uploadFile(
  item: QueueItem,
  patientId: string,
  accessToken: string | null,
  clinicId: string,
  onProgress: (pct: number) => void,
  onDone: () => void,
  onError: (msg: string) => void,
): XMLHttpRequest {
  const fd = new FormData();
  fd.append('file', item.file);
  fd.append('kind', item.kind);
  fd.append('patient_id', patientId);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/v2/clinical/documents/upload');
  xhr.setRequestHeader('X-Clinic-Id', clinicId);
  if (accessToken) xhr.setRequestHeader('Authorization', `Bearer ${accessToken}`);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
  };
  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) onDone();
    else onError(xhr.statusText || 'Upload failed');
  };
  xhr.onerror = () => onError('Network error');
  xhr.send(fd);
  return xhr;
}

export default function DocumentUploader({ patientId, defaultKind = 'other' }: DocumentUploaderProps) {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [globalKind, setGlobalKind] = useState<DocKind>(defaultKind);
  const qc = useQueryClient();
  const { accessToken, clinicId } = useAuthStore();

  function updateItem(id: string, patch: Partial<QueueItem>) {
    setQueue((q) => q.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  function startUpload(item: QueueItem) {
    updateItem(item.id, { status: 'uploading', progress: 0, error: undefined });
    uploadFile(
      item,
      patientId,
      accessToken,
      clinicId,
      (pct) => updateItem(item.id, { progress: pct }),
      () => {
        updateItem(item.id, { status: 'done', progress: 100 });
        void qc.invalidateQueries({ queryKey: ['documents', patientId] });
        setTimeout(() => setQueue((q) => q.filter((i) => i.id !== item.id)), 2000);
      },
      (msg) => updateItem(item.id, { status: 'error', error: msg }),
    );
  }

  const onDrop = useCallback(
    (accepted: File[]) => {
      const capped = accepted.slice(0, 10);
      const newItems: QueueItem[] = capped.map((file) => ({
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        file,
        kind: globalKind,
        progress: 0,
        status: 'pending',
      }));
      setQueue((q) => [...q, ...newItems]);
      newItems.forEach((item) => startUpload(item));
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [globalKind, patientId, accessToken, clinicId],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      'image/*': [],
      'application/pdf': [],
      'application/msword': [],
    },
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <label htmlFor="doc-kind" className="text-sm text-zinc-700">Kind:</label>
        <select
          id="doc-kind"
          value={globalKind}
          onChange={(e) => setGlobalKind(e.target.value as DocKind)}
          className="rounded border border-zinc-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
        >
          <option value="photo">Photo</option>
          <option value="xray">X-Ray</option>
          <option value="consent">Consent</option>
          <option value="insurance">Insurance</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div
        {...getRootProps()}
        data-testid="dropzone"
        className={`flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed px-4 py-8 text-sm transition-colors ${isDragActive ? 'border-zinc-500 bg-zinc-50' : 'border-zinc-300 hover:border-zinc-400'}`}
      >
        <input {...getInputProps()} data-testid="file-input" />
        <span className="text-zinc-500">
          {isDragActive ? 'Drop files here…' : 'Drag & drop or click to choose files (up to 10)'}
        </span>
      </div>

      {queue.length > 0 && (
        <ul data-testid="upload-queue" className="space-y-2">
          {queue.map((item) => (
            <li key={item.id} className="rounded border border-zinc-200 px-3 py-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{item.file.name}</span>
                {item.status === 'done' && (
                  <span className="text-green-600" data-testid={`status-done-${item.file.name}`}>✓</span>
                )}
                {item.status === 'error' && (
                  <button
                    onClick={() => startUpload(item)}
                    className="text-xs text-red-600 underline"
                  >
                    Retry
                  </button>
                )}
              </div>
              {item.status === 'error' && (
                <p className="mt-1 text-xs text-red-600">{item.error}</p>
              )}
              {(item.status === 'uploading' || item.status === 'done') && (
                <div className="mt-1 h-1.5 w-full rounded bg-zinc-200">
                  <div
                    data-testid={`progress-bar-${item.file.name}`}
                    className={`h-full rounded transition-all ${item.status === 'done' ? 'bg-green-500' : 'bg-zinc-900'}`}
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
