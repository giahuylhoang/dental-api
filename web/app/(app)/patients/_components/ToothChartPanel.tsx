"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetcher } from "@/lib/api/client";

type ToothStatus = "present" | "missing" | "extracted" | "implant" | "crowned" | "filled";

const STATUS_OPTIONS: ToothStatus[] = ["present", "missing", "extracted", "implant", "crowned", "filled"];

const STATUS_COLOR: Record<ToothStatus, string> = {
  present: "bg-muted border-border",
  missing: "bg-transparent border-dashed border-muted-foreground",
  extracted: "bg-red-50 border-destructive",
  implant: "bg-blue-50 border-blue-500",
  crowned: "bg-amber-50 border-amber-500",
  filled: "bg-cyan-50 border-cyan-500",
};

const TOP_ROW = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
const BOTTOM_ROW = [32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17];

interface ToothEntry {
  tooth_number: number;
  status: string;
  surface_notes?: Record<string, string> | null;
}

interface Popover {
  toothNumber: number;
  status: ToothStatus;
  notes: string;
}

export function ToothChartPanel({ patientId }: { patientId: string }) {
  const qc = useQueryClient();
  const [popover, setPopover] = useState<Popover | null>(null);

  const { data: chart = [], isLoading } = useQuery<ToothEntry[]>({
    queryKey: ["tooth-chart", patientId],
    queryFn: () => fetcher<ToothEntry[]>(`/api/v2/clinical/patients/${patientId}/tooth-chart`),
  });

  const saveMutation = useMutation({
    mutationFn: (entry: { tooth_number: number; status: string; surface_notes: Record<string, string> | null }) =>
      fetcher<ToothEntry[]>(`/api/v2/clinical/patients/${patientId}/tooth-chart`, { method: "POST", body: JSON.stringify([entry]) }),
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ["tooth-chart", patientId] }); setPopover(null); },
  });

  function getStatus(n: number): ToothStatus {
    return (chart.find((e) => e.tooth_number === n)?.status as ToothStatus) ?? "present";
  }

  function handleClick(n: number) {
    const entry = chart.find((e) => e.tooth_number === n);
    setPopover({ toothNumber: n, status: (entry?.status as ToothStatus) ?? "present", notes: entry?.surface_notes?.notes ?? "" });
  }

  function Tooth({ n }: { n: number }) {
    const st = getStatus(n);
    return (
      <button onClick={() => handleClick(n)} className={`flex flex-col items-center gap-0.5 group`} aria-label={`Tooth ${n}`}>
        <div className={`w-5 h-6 rounded-sm border-2 transition-colors group-hover:opacity-70 ${STATUS_COLOR[st]}`} />
        <span className="font-mono text-[0.55rem] text-muted-foreground">{n}</span>
      </button>
    );
  }

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-[repeat(16,1fr)] gap-1">
        {TOP_ROW.map((n) => <Tooth key={n} n={n} />)}
      </div>
      <div className="h-px bg-border" />
      <div className="grid grid-cols-[repeat(16,1fr)] gap-1">
        {BOTTOM_ROW.map((n) => <Tooth key={n} n={n} />)}
      </div>
      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        {STATUS_OPTIONS.map((s) => (
          <span key={s} className="inline-flex items-center gap-1">
            <span className={`w-2.5 h-2.5 rounded-sm border-2 ${STATUS_COLOR[s]}`} /> {s}
          </span>
        ))}
      </div>
      {popover && (
        <div className="rounded border border-border bg-card p-4 shadow-md">
          <h4 className="mb-3 text-sm font-medium">Tooth #{popover.toothNumber}</h4>
          <div className="space-y-3">
            <div>
              <label htmlFor="tooth-status" className="mb-1 block text-xs text-muted-foreground">Status</label>
              <select id="tooth-status" value={popover.status} onChange={(e) => setPopover((p) => p ? { ...p, status: e.target.value as ToothStatus } : p)} className="rounded border border-border bg-background px-2 py-1.5 text-sm outline-none focus:border-primary">
                {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="tooth-notes" className="mb-1 block text-xs text-muted-foreground">Notes</label>
              <input id="tooth-notes" value={popover.notes} onChange={(e) => setPopover((p) => p ? { ...p, notes: e.target.value } : p)} className="w-full rounded border border-border bg-background px-2 py-1.5 text-sm outline-none focus:border-primary" />
            </div>
            <div className="flex gap-2">
              <button onClick={() => saveMutation.mutate({ tooth_number: popover.toothNumber, status: popover.status, surface_notes: popover.notes ? { notes: popover.notes } : null })} disabled={saveMutation.isPending} className="rounded bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-80 disabled:opacity-50">Save</button>
              <button onClick={() => setPopover(null)} className="rounded border border-border px-3 py-1.5 text-sm hover:bg-muted">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
