import React from "react";

export interface FormFieldProps {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}

export function FormField({ label, hint, error, children }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1 mb-3.5">
      <label className={`text-xs font-medium uppercase tracking-wide ${error ? "text-destructive" : "text-foreground"}`}>
        {label}
      </label>
      {children}
      {hint && !error && <span className="text-xs text-muted-foreground">{hint}</span>}
      {error && <span className="text-xs text-destructive">{error}</span>}
    </div>
  );
}
