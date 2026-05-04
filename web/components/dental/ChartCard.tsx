export interface ChartCardProps {
  title: string;
  value: string | number;
  delta?: number;
  trend?: number[];
  unit?: string;
}

export function ChartCard({ title, value, delta, trend, unit }: ChartCardProps) {
  const sparkline =
    trend && trend.length > 1
      ? (() => {
          const W = 80, H = 28;
          const min = Math.min(...trend), max = Math.max(...trend);
          const range = max - min || 1;
          const pts = trend
            .map((v, i) => {
              const x = (i / (trend.length - 1)) * W;
              const y = H - ((v - min) / range) * H;
              return `${x},${y}`;
            })
            .join(" ");
          return (
            <svg width={W} height={H} className="block">
              <polyline points={pts} fill="none" stroke="hsl(var(--primary))" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
          );
        })()
      : null;

  const deltaClass = delta != null && delta > 0 ? "text-green-700" : delta != null && delta < 0 ? "text-destructive" : "text-muted-foreground";
  const deltaSign = delta != null && delta > 0 ? "+" : "";

  return (
    <div className="bg-card border border-border rounded-md px-5 py-4 shadow-sm flex flex-col gap-1.5">
      <div className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{title}</div>
      <div className="flex items-end justify-between gap-2">
        <div>
          <span className="font-display font-extrabold text-3xl text-foreground tracking-tight">{value}</span>
          {unit && <span className="text-sm text-muted-foreground ml-1">{unit}</span>}
          {delta != null && (
            <div className={`text-xs mt-0.5 ${deltaClass}`}>{deltaSign}{delta}%</div>
          )}
        </div>
        {sparkline}
      </div>
    </div>
  );
}
