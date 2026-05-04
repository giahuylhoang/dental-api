"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetcher } from "@/lib/api/client";

const STATUS_OPTIONS = ["active", "inactive", "deceased", "merged", "pending"] as const;
type PatientStatusValue = (typeof STATUS_OPTIONS)[number];

interface PatientStatus {
  status: string;
  can_promote?: boolean;
}

export function LifecyclePanel({ patientId }: { patientId: string }) {
  const qc = useQueryClient();
  const [pendingStatus, setPendingStatus] = useState<PatientStatusValue | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const { data, isLoading } = useQuery<PatientStatus>({
    queryKey: ["patient-status", patientId],
    queryFn: () => fetcher<PatientStatus>(`/api/v2/clinical/patients/${patientId}/status`),
  });

  const promoteMutation = useMutation({
    mutationFn: () => fetcher<PatientStatus>(`/api/v2/clinical/patients/${patientId}/promote`, { method: "POST" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["patient-status", patientId] });
      void qc.invalidateQueries({ queryKey: ["patient", patientId] });
    },
  });

  const statusMutation = useMutation({
    mutationFn: (status: string) =>
      fetcher<PatientStatus>(`/api/v2/clinical/patients/${patientId}/status`, { method: "PUT", body: JSON.stringify({ status }) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["patient-status", patientId] });
      void qc.invalidateQueries({ queryKey: ["patient", patientId] });
      setConfirmOpen(false);
      setPendingStatus(null);
    },
  });

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;

  const currentStatus = data?.status ?? "unknown";
  const canPromote = data?.can_promote ?? currentStatus !== "active";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-foreground">Current status:</span>
        <span className="rounded-full bg-muted px-3 py-1 text-sm font-medium capitalize text-foreground">{currentStatus}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => promoteMutation.mutate()}
          disabled={currentStatus === "active" || !canPromote || promoteMutation.isPending}
          className="rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Promote to active
        </button>
        <div className="flex items-center gap-2">
          <label htmlFor="status-select" className="text-sm text-muted-foreground">Change status:</label>
          <select
            id="status-select"
            value=""
            onChange={(e) => { setPendingStatus(e.target.value as PatientStatusValue); setConfirmOpen(true); }}
            className="rounded border border-border bg-background px-2 py-1.5 text-sm outline-none focus:border-primary"
          >
            <option value="" disabled>Select…</option>
            {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>
      {promoteMutation.isError && <p className="text-sm text-destructive">{(promoteMutation.error as Error).message}</p>}
      {confirmOpen && pendingStatus && (
        <div className="rounded border border-border bg-muted/30 p-4">
          <p className="mb-3 text-sm">Change status to <strong>{pendingStatus}</strong>?</p>
          <div className="flex gap-2">
            <button onClick={() => statusMutation.mutate(pendingStatus)} disabled={statusMutation.isPending} className="rounded bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-80 disabled:opacity-50">Confirm</button>
            <button onClick={() => { setConfirmOpen(false); setPendingStatus(null); }} className="rounded border border-border px-3 py-1.5 text-sm hover:bg-muted">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
