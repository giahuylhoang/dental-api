"use client";

import { useState, useEffect } from "react";
import { Bell, Search } from "lucide-react";
import Link from "next/link";

export interface TopBarProps {
  clinicName?: string;
  breadcrumb?: string[];
  homeHref?: string;
  mode?: string;
  onSearch?: () => void;
  onNotifications?: () => void;
  onProfile?: () => void;
  userName?: string;
  userEmail?: string;
  role?: string;
}

export function TopBar({
  clinicName = "Oak Dental · Calgary",
  breadcrumb = ["Dashboard"],
  homeHref = "/dashboard",
  mode,
  onSearch,
  onNotifications,
  userName = "Demo Clinician",
  userEmail = "",
  role = "Demo",
}: TopBarProps) {
  const initials = userName.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      const pill = document.getElementById("rrd-profile-pill");
      const menu = document.getElementById("rrd-profile-menu");
      if (pill?.contains(e.target as Node)) return;
      if (menu?.contains(e.target as Node)) return;
      setMenuOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [menuOpen]);

  return (
    <header className="h-16 px-7 bg-card border-b border-border flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-3.5">
        <Link href={homeHref} className="no-underline">
          <span className="font-display font-bold text-sm text-foreground tracking-tight">{clinicName}</span>
        </Link>
        {mode && (
          <span className="inline-flex items-center gap-1.5 bg-primary text-primary-foreground text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded-full">
            <span className="w-2.5 h-2.5 rounded-full bg-primary-foreground/30" />
            {mode}
          </span>
        )}
        <span className="w-px h-4 bg-border" />
        <nav className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          {breadcrumb.map((b, i) => (
            <span key={i} className="flex items-center gap-2">
              {i > 0 && <span className="text-border">›</span>}
              <span className={i === breadcrumb.length - 1 ? "text-foreground font-medium" : ""}>{b}</span>
            </span>
          ))}
        </nav>
      </div>
      <div className="flex items-center gap-2.5">
        <button
          onClick={onSearch}
          className="inline-flex items-center gap-2 bg-muted border border-border rounded-md px-3 py-1.5 cursor-pointer text-muted-foreground text-sm hover:bg-muted/80 transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          Search
          <span className="font-mono text-xs text-muted-foreground px-1.5 py-0.5 bg-border rounded">⌘K</span>
        </button>
        <button
          onClick={onNotifications}
          className="w-9 h-9 rounded-md bg-muted border border-border cursor-pointer text-muted-foreground inline-flex items-center justify-center relative hover:bg-muted/80 transition-colors"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-2 w-1.5 h-1.5 rounded-full bg-destructive" />
        </button>
        <div className="relative">
          <button
            id="rrd-profile-pill"
            type="button"
            aria-expanded={menuOpen}
            aria-controls="rrd-profile-menu"
            onClick={() => setMenuOpen((o) => !o)}
            className="w-9 h-9 rounded-full bg-primary text-primary-foreground border-none cursor-pointer font-semibold text-sm"
          >
            {initials}
          </button>
          {menuOpen && (
            <div
              id="rrd-profile-menu"
              role="menu"
              className="absolute top-full right-0 mt-1.5 w-60 bg-card border border-border rounded-md shadow-xl z-30 p-1"
            >
              <div className="px-3.5 py-3">
                <div className="font-semibold text-base text-foreground">{userName}</div>
                <div className="font-mono text-xs text-muted-foreground mt-0.5">{userEmail}</div>
                <span className={`inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${role === "Owner" ? "bg-blue-50 text-blue-700" : "bg-muted text-muted-foreground"}`}>
                  {role}
                </span>
              </div>
              <div className="h-px bg-border my-1" />
              <Link href="/settings" role="menuitem" className="block px-3.5 py-2.5 text-sm text-foreground no-underline rounded hover:bg-muted transition-colors">
                Account
              </Link>
              <Link href="/login?logout=1" role="menuitem" className="block px-3.5 py-2.5 text-sm text-destructive no-underline rounded hover:bg-muted transition-colors">
                Sign out
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
