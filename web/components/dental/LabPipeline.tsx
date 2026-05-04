"use client";

export interface LabCase {
  id: string;
  patient: string;
  vendor: string;
  item: string;
  eta: string;
  col: string;
}

export interface LabColumn {
  id: string;
  label: string;
}

const LAB_COLUMNS: LabColumn[] = [
  { id: "sent",     label: "Sent · waiting on lab" },
  { id: "progress", label: "In progress" },
  { id: "returned", label: "Returned · ready to seat" },
];

const LAB_CASES: LabCase[] = [
  { id: "LC-2026-0481", patient: "Alice Stevens",  vendor: "Pinnacle Dental Lab",   item: "Crown · #36",            eta: "2026-05-12", col: "sent" },
  { id: "LC-2026-0476", patient: "Sofía Castillo", vendor: "Crown City Lab",        item: "Implant · #11",          eta: "2026-05-18", col: "sent" },
  { id: "LC-2026-0474", patient: "Marcus Doan",    vendor: "Mountain Lab Services", item: "Reline · upper denture", eta: "2026-05-08", col: "progress" },
  { id: "LC-2026-0469", patient: "Priya Khanna",   vendor: "Pinnacle Dental Lab",   item: "Crown · #36",            eta: "2026-05-04", col: "returned" },
  { id: "LC-2026-0467", patient: "Eli Brouwer",    vendor: "Apex Ortho Lab",        item: "Retainer",               eta: "2026-05-04", col: "returned" },
];

export interface LabPipelineProps {
  cases?: LabCase[];
  columns?: LabColumn[];
  onCaseClick?: (c: LabCase) => void;
}

export function LabPipeline({ cases = LAB_CASES, columns = LAB_COLUMNS, onCaseClick }: LabPipelineProps) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {columns.map((col) => {
        const cards = cases.filter((c) => c.col === col.id);
        return (
          <div key={col.id} className="bg-muted border border-border rounded-md p-3 flex flex-col gap-2 min-h-60">
            <div className="flex justify-between items-center px-1.5 pb-2">
              <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{col.label}</span>
              <span className="font-mono text-xs text-primary font-semibold px-2 py-0.5 bg-primary/10 rounded-full">{cards.length}</span>
            </div>
            {cards.map((c) => (
              <div
                key={c.id}
                className="bg-card border border-border rounded-md px-3.5 py-3 flex flex-col gap-1.5 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => onCaseClick?.(c)}
              >
                <div className="flex justify-between items-start gap-2">
                  <div className="font-semibold text-sm text-foreground">{c.patient}</div>
                  <span className="font-mono text-xs text-muted-foreground">{c.id}</span>
                </div>
                <div className="text-sm text-muted-foreground">{c.item}</div>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-xs text-muted-foreground">{c.vendor}</span>
                  <span className="font-mono text-xs text-amber-700">ETA {c.eta}</span>
                </div>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
