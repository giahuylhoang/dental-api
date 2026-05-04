import React from "react";

export interface MonoTextProps {
  children: React.ReactNode;
  className?: string;
}

export function MonoText({ children, className }: MonoTextProps) {
  return (
    <span className={`font-mono tracking-wide ${className ?? ""}`}>
      {children}
    </span>
  );
}
