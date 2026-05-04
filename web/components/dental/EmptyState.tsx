import React from "react";
import { Info } from "lucide-react";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  body: string;
  ctaLabel?: string;
  onCta?: () => void;
}

export function EmptyState({ icon, title, body, ctaLabel, onCta }: EmptyStateProps) {
  return (
    <div className="bg-card border border-dashed border-border rounded-md px-8 py-10 flex flex-col items-center gap-3 text-center text-muted-foreground">
      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center text-primary">
        {icon ?? <Info className="w-5 h-5" />}
      </div>
      <div className="font-display font-bold text-lg text-foreground">{title}</div>
      <div className="text-sm max-w-sm leading-relaxed">{body}</div>
      {ctaLabel && (
        <button onClick={onCta} className="mt-1.5 bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-semibold hover:opacity-90 transition-opacity">
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
