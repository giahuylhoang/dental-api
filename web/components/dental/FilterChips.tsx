"use client";

export interface FilterChip {
  key: string;
  label: string;
  count?: number;
}

export interface FilterChipsProps {
  chips: FilterChip[];
  active: string;
  onChange: (key: string) => void;
}

export function FilterChips({ chips, active, onChange }: FilterChipsProps) {
  return (
    <div className="flex gap-1.5 flex-wrap items-center">
      {chips.map((chip) => (
        <button
          key={chip.key}
          onClick={() => onChange(chip.key)}
          className={`inline-flex items-center gap-1.5 h-8 px-3 rounded-full border text-xs transition-colors ${
            chip.key === active
              ? "border-border bg-muted text-foreground font-semibold"
              : "border-border bg-card text-muted-foreground font-normal hover:bg-muted/50"
          }`}
        >
          {chip.label}
          {chip.count != null && (
            <span className="font-mono text-xs">{chip.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
