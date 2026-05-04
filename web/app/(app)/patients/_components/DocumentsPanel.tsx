"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetcher } from "@/lib/api/client";
import { useAuthStore } from "@/lib/auth/store";

type DocKind = "photo" | "xray" | "consent" | "insurance" | "other";

interface QueueItem {
  id: string;
  file: File;
  kind: DocKind;
  progress: number;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
}

interface Document {
  id: string;
  kind: string;
  storage_url: string;
  created_at?: string | null;
  size_bytes?: number | null;
}

const KIND_LABELS: Record<string, string> = {
  photo: "Photos", xray: "X-Rays", consent: "Consent Forms", insurance: "Insurance", other: "Other",
};

function uploadFile(
  item: QueueItem,
  patientId: string,
  accessToken: string | null,
  clinicId: string,
  onProgress: (pct: number) => void,
  onDone: () => void,
  onError: (msg: string) => void,
) {
  const fd = new FormData();
  fd.append("file", item.file);
  fd.append("kind", item.kind);
  fd.append("patient_id", patientId);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/v2/clinical/documents/upload");
  xhr.setRequestHeader("X-Clinic-Id", clinicId);
  if (accessToken) xhr.setRequestHeader("Authorization", `Bearer ${accessToken}`);
  xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100)); };
  xhr.onload = () => { if (xhr.status >= 200 && xhr.status < 300) onDone(); else onError(xhr.statusText || "Upload failed"); };
  xhr.onerror = () => onError("Network error");
  xhr.send(fd);
}

export function DocumentsPanel({ patientId }: { patientId: string }) {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [globalKind, setGlobalKind] = useState<DocKind>("other");
  const qc = useQueryClient();
  const { accessToken, clinicId } = useAuthStore();

  const { data: docs = [], isLoading } = useQuery<Document[]>({
    queryKey: ["documents", patientId],
    queryFn: () => fetcher<Document[]>(`/api/v2/clinical/patients/${patientId}/documents`),
  });

  function updateItem(id: string, patch: Partial<QueueItem>) {
    setQueue((q) => q.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  function startUpload(item: QueueItem) {
    updateItem(item.id, { status: "uploading", progress: 0, error: undefined });
    uploadFile(
      item, patientId, accessToken, clinicId,
      (pct) => updateItem(item.id, { progress: pct }),
      () => {
        updateItem(item.id, { status: "done", progress: 100 });
        void qc.invalidateQueries({ queryKey: ["documents", patientId] });
        setTimeout(() => setQueue((q) => q.filter((i) => i.id !== item.id)), 2000);
      },
      (msg) => updateItem(item.id, { status: "error", error: msg }),
    );
  }

  const onDrop = useCallback(
    (accepted: File[]) => {
      const newItems: QueueItem[] = accepted.slice(0, 10).map((file) => ({
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        file, kind: globalKind, progress: 0, status: "pending",
      }));
      setQueue((q) => [...q, ...newItems]);
      newItems.forEach((item) => startUpload(item));
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [globalKind, patientId, accessToken, clinicId],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, multiple: true,
    accept: { "image/*": [], "application/pdf": [], "application/msword": [] },
  });

  const grouped = docs.reduce<Record<string, Document[]>>((acc, doc) => {
    if (!acc[doc.kind]) acc[doc.kind] = [];
    acc[doc.kind].push(doc);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label htmlFor="doc-kind" className="text-sm text-muted-foreground">Kind:</label>
        <select id="doc-kind" value={globalKind} onChange={(e) => setGlobalKind(e.target.value as DocKind)} className="rounded border border-border bg-background px-2 py-1.5 text-sm outline-none focus:border-primary">
          <option value="photo">Photo</option>
          <option value="xray">X-Ray</option>
          <option value="consent">Consent</option>
          <option value="insurance">Insurance</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div {...getRootProps()} className={`flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed px-4 py-8 text-sm transition-colors ${isDragActive ? "border-foreground bg-muted/40" : "border-border hover:border-muted-foreground"}`}>
        <input {...getInputProps()} />
        <span className="text-muted-foreground">{isDragActive ? "Drop files here…" : "Drag & drop or click to choose files (up to 10)"}</span>
      </div>
      {queue.length > 0 && (
        <ul className="space-y-2">
          {queue.map((item) => (
            <li key={item.id} className="rounded border border-border px-3 py-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{item.file.name}</span>
                {item.status === "done" && <span className="text-green-600">✓</span>}
                {item.status === "error" && <button onClick={() => startUpload(item)} className="text-xs text-destructive underline">Retry</button>}
              </div>
              {item.status === "error" && <p className="mt-1 text-xs text-destructive">{item.error}</p>}
              {(item.status === "uploading" || item.status === "done") && (
                <progress
                  className="mt-1 h-1.5 w-full rounded"
                  value={item.progress}
                  max={100}
                  aria-label="Upload progress"
                />
              )}
            </li>
          ))}
        </ul>
      )}
      {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
      {!isLoading && Object.entries(grouped).map(([kind, items]) => (
        <div key={kind}>
          <h4 className="mb-2 text-sm font-medium text-foreground">{KIND_LABELS[kind] ?? kind}</h4>
          <div className="space-y-1">
            {items.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between rounded border border-border px-3 py-2 text-sm">
                <a href={doc.storage_url} target="_blank" rel="noopener noreferrer" className="font-medium text-foreground hover:underline">
                  {doc.storage_url.split("/").pop() ?? doc.id}
                </a>
                <div className="flex items-center gap-3 text-muted-foreground">
                  <span>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "—"}</span>
                  <span>{doc.size_bytes ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : "—"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
