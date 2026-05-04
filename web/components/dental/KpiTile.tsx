export interface KpiTileProps {
  label: string;
  value: string | number;
  delta?: string;
  trend?: "up" | "down" | "flat";
  accent?: "steel" | "navy";
}

export function KpiTile({ label, value, delta, trend = "up", accent = "steel" }: KpiTileProps) {
  const accentClass = accent === "navy" ? "text-foreground" : "text-primary";
  const dClass = trend === "up" ? "text-green-700" : trend === "down" ? "text-destructive" : "text-muted-foreground";
  const arrow = trend === "up" ? "▲" : trend === "down" ? "▼" : "·";

  return (
    <div className="bg-card border border-border rounded-md px-5 py-5 shadow-sm flex flex-col gap-1.5">
      <span className={`text-xs font-semibold uppercase tracking-widest ${accentClass}`}>{label}</span>
      <span className="font-mono text-3xl font-semibold text-foreground tracking-tight leading-tight">{value}</span>
      {delta != null && (
        <span className={`inline-flex gap-1.5 items-center text-sm font-medium ${dClass}`}>
          <span>{arrow}</span>
          <span>{delta}</span>
          <span className="text-muted-foreground font-normal">vs last week</span>
        </span>
      )}
    </div>
  );
}
