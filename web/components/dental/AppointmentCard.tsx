"use client";

export interface Appointment {
  time: string;
  duration: number;
  patient: string;
  kind: string;
  provider: string;
  chair: string | number;
  status: "confirmed" | "pending" | "no_show" | "completed";
}

export interface AppointmentCardProps {
  appointment: Appointment;
  onClick?: () => void;
  expanded?: boolean;
}

const STATUS_TONE: Record<string, { bg: string; fg: string; label: string }> = {
  confirmed: { bg: "bg-green-50", fg: "text-green-700", label: "Confirmed" },
  pending:   { bg: "bg-amber-50", fg: "text-amber-700", label: "Pending" },
  no_show:   { bg: "bg-red-50",   fg: "text-red-700",   label: "No-show" },
  completed: { bg: "bg-muted",    fg: "text-muted-foreground", label: "Completed" },
};

export function AppointmentCard({ appointment: a, onClick, expanded }: AppointmentCardProps) {
  const tone = STATUS_TONE[a.status] ?? STATUS_TONE.confirmed;
  const initials = a.patient.split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();
  return (
    <div
      onClick={onClick}
      className={`bg-card border rounded-md px-4 py-3 grid grid-cols-[64px_32px_1fr_auto] gap-3 items-center cursor-pointer transition-shadow ${
        expanded ? "border-primary shadow-lg" : "border-border hover:shadow-md"
      }`}
    >
      <div className="flex flex-col items-start">
        <span className="font-mono font-semibold text-base text-foreground">{a.time}</span>
        <span className="text-xs text-muted-foreground">{a.duration} min</span>
      </div>
      <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold text-xs">
        {initials}
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="font-semibold text-sm text-foreground truncate">{a.patient}</span>
        <span className="text-xs text-muted-foreground">{a.kind} · {a.provider} · Op {a.chair}</span>
      </div>
      <span className={`text-xs font-semibold px-2.5 py-0.5 rounded uppercase tracking-wide ${tone.bg} ${tone.fg}`}>
        {tone.label}
      </span>
    </div>
  );
}
