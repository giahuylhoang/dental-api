"use client";

import React from "react";
import Link from "next/link";

export interface IconButtonProps {
  label: string;
  onClick?: () => void;
  href?: string;
  variant?: "ghost" | "primary";
  children: React.ReactNode;
}

export function IconButton({ label, onClick, href, variant = "ghost", children }: IconButtonProps) {
  const base = "w-8 h-8 rounded inline-flex items-center justify-center cursor-pointer transition-colors no-underline";
  const cls = variant === "primary"
    ? `${base} bg-primary text-primary-foreground hover:opacity-85`
    : `${base} bg-transparent text-muted-foreground hover:bg-muted`;

  if (href) {
    return <Link href={href} aria-label={label} className={cls}>{children}</Link>;
  }
  return (
    <button onClick={onClick} aria-label={label} className={cls}>
      {children}
    </button>
  );
}
