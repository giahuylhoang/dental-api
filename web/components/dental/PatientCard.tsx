"use client";

export interface Patient {
  id: string;
  first: string;
  last: string;
  dob: string;
  insurance: string;
  status: "active" | "recall" | "plan" | "inactive";
}

export interface PatientCardProps {
  patient: Patient;
  density?: "comfortable" | "compact";
  onClick?: () => void;
}

const STATUS_BG: Record<string, string> = {
  active:   "bg-blue-600",
  recall:   "bg-amber-700",
  plan:     "bg-blue-400",
  inactive: "bg-slate-400",
};

const STATUS_PILL: Record<string, string> = {
  active:   "bg-green-50 text-green-700",
  recall:   "bg-amber-50 text-amber-700",
  plan:     "bg-muted text-muted-foreground",
  inactive: "bg-muted text-muted-foreground",
};

export function PatientCard({ patient, density = "comfortable", onClick }: PatientCardProps) {
  const initials = ((patient.first?.[0] ?? "?") + (patient.last?.[0] ?? "?")).toUpperCase();
  const compact = density === "compact";
  const bg = STATUS_BG[patient.status] ?? "bg-primary";

  return (
    <div
      onClick={onClick}
      className={`bg-card border border-border rounded-md grid grid-cols-[40px_1fr_auto] gap-3.5 items-center cursor-pointer transition-shadow hover:shadow-lg ${compact ? "px-3.5 py-3" : "px-4 py-4"}`}
    >
      <div className={`w-10 h-10 rounded-full text-white flex items-center justify-center font-semibold text-sm ${bg}`}>
        {initials}
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <div className="font-semibold text-sm text-foreground truncate">{patient.first} {patient.last}</div>
        <div className="font-mono text-xs text-muted-foreground flex gap-2">
          <span>{patient.id}</span>
          <span>·</span>
          <span>{patient.dob}</span>
          <span>·</span>
          <span className="font-sans text-muted-foreground">{patient.insurance}</span>
        </div>
      </div>
      <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full uppercase tracking-wide ${STATUS_PILL[patient.status] ?? "bg-muted text-muted-foreground"}`}>
        {patient.status}
      </span>
    </div>
  );
}
