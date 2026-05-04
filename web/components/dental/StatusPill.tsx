type ToneKey = "success" | "warn" | "danger" | "info" | "muted" | "default";

const TONES: Record<ToneKey, { bg: string; color: string }> = {
  success: { bg: "bg-green-50",  color: "text-green-700" },
  warn:    { bg: "bg-amber-50",  color: "text-amber-700" },
  danger:  { bg: "bg-red-50",    color: "text-destructive" },
  info:    { bg: "bg-blue-50",   color: "text-blue-700" },
  muted:   { bg: "bg-muted",     color: "text-muted-foreground" },
  default: { bg: "bg-muted",     color: "text-muted-foreground" },
};

const MAP: Record<string, Record<string, ToneKey>> = {
  lead: { NEW: "info", CONTACTED: "warn", QUALIFIED: "success", CONVERTED: "success", LOST: "danger" },
  claim: { draft: "muted", submitted: "info", accepted: "success", adjudicated: "warn", paid: "success", rejected: "danger", partial: "warn" },
  invoice: { draft: "muted", issued: "info", partial: "warn", paid: "success", void: "danger", overdue: "danger" },
  appointment: { SCHEDULED: "info", CONFIRMED: "success", COMPLETED: "success", NO_SHOW: "danger", PENDING: "warn", PENDING_SYNC: "warn", RESCHEDULED: "warn", REMINDER_SENT: "info", CANCELLED: "danger" },
  lab_case: { draft: "muted", sent: "warn", in_progress: "info", returned: "success", remake: "danger", cancelled: "danger" },
  denture_case: { open: "info", closed: "muted" },
  treatment_plan: { draft: "muted", presented: "info", accepted: "success", in_progress: "warn", completed: "success", declined: "danger" },
  patient_lifecycle: { pending: "warn", active: "success", inactive: "muted", deceased: "danger", merged: "muted" },
  recall: { pending: "warn", sent: "info", completed: "success", cancelled: "danger" },
};

export interface StatusPillProps {
  kind: string;
  value: string;
}

export function StatusPill({ kind, value }: StatusPillProps) {
  const toneKey: ToneKey = (MAP[kind]?.[value]) ?? "default";
  const tone = TONES[toneKey];
  return (
    <span className={`inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full uppercase tracking-wide ${tone.bg} ${tone.color}`}>
      {value}
    </span>
  );
}
