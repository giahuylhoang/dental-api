"use client";

import { Search } from "lucide-react";

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchInput({ value, onChange, placeholder = "Search…" }: SearchInputProps) {
  return (
    <div className="relative inline-flex items-center">
      <Search className="absolute left-3 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-9 pl-9 pr-3 rounded border border-border bg-muted text-sm text-foreground outline-none min-w-56 focus:border-primary transition-colors"
      />
    </div>
  );
}
