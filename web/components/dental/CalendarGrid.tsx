import React from "react";

export interface CalendarColumn {
  key: string;
  label: string;
}

export interface CalendarEvent {
  columnKey: string;
  start: string; // "HH:MM"
  end: string;   // "HH:MM"
  color?: string;
  render?: (ev: CalendarEvent) => React.ReactNode;
}

export interface CalendarGridProps {
  slotMinutes?: number;
  dayStartHour?: number;
  dayEndHour?: number;
  columns: CalendarColumn[];
  events: CalendarEvent[];
  nowMinutes?: number;
}

const ROW_H = 36;

function toPercent(timeStr: string, startH: number, totalMins: number): number {
  const [h, m] = timeStr.split(":").map(Number);
  return ((h * 60 + m - startH * 60) / totalMins) * 100;
}

export function CalendarGrid({
  slotMinutes = 30,
  dayStartHour = 8,
  dayEndHour = 18,
  columns,
  events,
  nowMinutes,
}: CalendarGridProps) {
  const startH = dayStartHour;
  const totalMins = (dayEndHour - startH) * 60;
  const slotCount = totalMins / slotMinutes;
  const colCount = columns.length;
  const colHeight = slotCount * (ROW_H + 1) + ROW_H + 1;
  const overlayNegMargin = -(slotCount * (ROW_H + 1) + ROW_H + 1);

  const slots: string[] = [];
  for (let i = 0; i <= slotCount; i++) {
    const m = startH * 60 + i * slotMinutes;
    const h = Math.floor(m / 60);
    const mm = m % 60;
    slots.push(`${String(h).padStart(2, "0")}:${String(mm).padStart(2, "0")}`);
  }

  const uid = `cg-${colCount}-${slotCount}`;

  return (
    <div>
      <style>{`
        .${uid}-grid { display: grid; grid-template-columns: 56px repeat(${colCount}, 1fr); gap: 1px; background: hsl(var(--border)); border: 1px solid hsl(var(--border)); border-radius: 4px; overflow: hidden; }
        .${uid}-row { min-height: ${ROW_H}px; }
        .${uid}-overlay { margin-top: ${overlayNegMargin}px; pointer-events: none; position: relative; }
        .${uid}-overlay-grid { display: grid; grid-template-columns: 56px repeat(${colCount}, 1fr); gap: 1px; }
        .${uid}-header-spacer { height: ${ROW_H + 1}px; }
        .${uid}-col { position: relative; pointer-events: auto; height: ${colHeight}px; }
        .${uid}-col-inner { position: absolute; top: ${ROW_H + 1}px; left: 0; right: 0; bottom: 0; }
      `}</style>

      <div className={`${uid}-grid`}>
        <div className="bg-card p-2.5" />
        {columns.map((col) => (
          <div key={col.key} className="bg-card px-3 py-2.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            {col.label}
          </div>
        ))}
        {slots.slice(0, -1).map((slot, si) => (
          <React.Fragment key={si}>
            <div className={`bg-card px-2.5 py-1 font-mono text-xs text-muted-foreground flex items-start ${uid}-row`}>
              {slot}
            </div>
            {columns.map((col) => (
              <div key={col.key} className={`bg-background relative ${uid}-row`} />
            ))}
          </React.Fragment>
        ))}
      </div>

      <div className={`${uid}-overlay`}>
        <div className={`${uid}-overlay-grid`}>
          <div className={`${uid}-header-spacer`} />
          {columns.map((col) => {
            const colEvents = events.filter((e) => e.columnKey === col.key);
            return (
              <div key={col.key} className={`${uid}-col`}>
                <div className={`${uid}-col-inner`}>
                  {colEvents.map((ev, ei) => {
                    const topPct = toPercent(ev.start, startH, totalMins);
                    const btmPct = toPercent(ev.end, startH, totalMins);
                    const evId = `ev-${uid}-${ei}`;
                    return (
                      <React.Fragment key={ei}>
                        <style>{`.${evId} { position: absolute; top: ${topPct}%; height: ${btmPct - topPct}%; left: 4px; right: 4px; border-radius: 4px; background: ${ev.color ?? "hsl(var(--muted))"}; padding: 6px 8px; cursor: pointer; overflow: hidden; }`}</style>
                        <div className={evId}>{ev.render ? ev.render(ev) : null}</div>
                      </React.Fragment>
                    );
                  })}
                  {nowMinutes != null && (() => {
                    const pct = ((nowMinutes - startH * 60) / totalMins) * 100;
                    if (pct < 0 || pct > 100) return null;
                    const nlId = `nl-${uid}`;
                    return (
                      <React.Fragment>
                        <style>{`.${nlId} { position: absolute; left: 0; right: 0; top: ${pct}%; height: 2px; background: hsl(var(--destructive)); z-index: 5; } .${nlId}-dot { position: absolute; left: -5px; top: -3px; width: 8px; height: 8px; border-radius: 999px; background: hsl(var(--destructive)); }`}</style>
                        <div className={nlId}><div className={`${nlId}-dot`} /></div>
                      </React.Fragment>
                    );
                  })()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
