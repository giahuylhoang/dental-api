type ToothStatus = "sound" | "caries" | "resto" | "crown" | "miss" | "endo";

const TOOTH_STATUS: Record<ToothStatus, { fill: string; stroke: string }> = {
  sound:  { fill: "bg-card",       stroke: "border-border" },
  caries: { fill: "bg-amber-50",   stroke: "border-amber-600" },
  resto:  { fill: "bg-blue-50",    stroke: "border-blue-500" },
  crown:  { fill: "bg-blue-200",   stroke: "border-blue-700" },
  miss:   { fill: "bg-muted",      stroke: "border-muted-foreground" },
  endo:   { fill: "bg-red-50",     stroke: "border-destructive" },
};

const MARKINGS: Record<number, ToothStatus> = {
  16: "resto", 17: "caries", 26: "crown", 27: "resto",
  36: "crown", 37: "caries", 46: "resto", 47: "sound",
  31: "sound", 41: "sound",  11: "sound", 21: "sound",
  18: "miss",  28: "miss",   38: "miss",  48: "miss",
};

function Tooth({ n }: { n: number }) {
  const st: ToothStatus = MARKINGS[n] ?? "sound";
  const tone = TOOTH_STATUS[st];
  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className={`w-5 h-7 rounded-t-md rounded-b-sm border-2 ${tone.fill} ${tone.stroke}`} />
      <span className="font-mono text-[0.6rem] text-muted-foreground">{n}</span>
    </div>
  );
}

export function ToothChartTile() {
  const upper = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lower = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  return (
    <div className="bg-card border border-border rounded-md p-4 shadow-sm">
      <div className="flex justify-between items-center mb-3">
        <span className="font-display font-bold text-sm text-foreground">Tooth chart</span>
        <span className="text-xs text-muted-foreground">FDI · Updated 2026-04-21</span>
      </div>
      <div className="grid grid-cols-[repeat(16,1fr)] gap-1">
        {upper.map((n) => <Tooth key={n} n={n} />)}
      </div>
      <div className="h-px bg-border my-2" />
      <div className="grid grid-cols-[repeat(16,1fr)] gap-1">
        {lower.map((n) => <Tooth key={n} n={n} />)}
      </div>
      <div className="flex flex-wrap gap-3 mt-3.5 text-xs text-muted-foreground">
        {(Object.entries(TOOTH_STATUS) as [ToothStatus, { fill: string; stroke: string }][]).map(([k, t]) => (
          <span key={k} className="inline-flex items-center gap-1">
            <span className={`w-2.5 h-2.5 rounded-sm border ${t.fill} ${t.stroke}`} /> {k}
          </span>
        ))}
      </div>
    </div>
  );
}
