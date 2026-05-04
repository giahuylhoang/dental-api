"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export interface NavProps {
  currentSection?: string;
  onNav?: (anchor: string) => void;
  dark?: boolean;
}

const LINKS = [
  { label: "Schedule", anchor: "schedule" },
  { label: "Chart",    anchor: "chart" },
  { label: "Lab",      anchor: "lab" },
  { label: "Pricing",  anchor: "pricing" },
  { label: "Contact",  anchor: "contact" },
];

export function Nav({ currentSection, onNav, dark = true }: NavProps) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const navBg = dark
    ? scrolled ? "bg-sidebar/92 backdrop-blur-md border-b border-white/10" : "bg-transparent"
    : scrolled ? "bg-card/92 backdrop-blur-md border-b border-border" : "bg-transparent";

  const linkBase = dark ? "text-sidebar-foreground/70 hover:text-sidebar-foreground" : "text-muted-foreground hover:text-foreground";
  const linkActive = dark ? "text-sidebar-foreground" : "text-foreground";

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-12 ${navBg}`}>
      <div className="max-w-6xl mx-auto flex items-center justify-between h-[72px]">
        <Link href="/" className="flex items-center gap-3 no-underline">
          <div className="flex flex-col leading-tight">
            <span className={`font-display font-extrabold text-lg tracking-widest uppercase ${dark ? "text-sidebar-foreground" : "text-foreground"}`}>ROCKYRIDGE</span>
            <span className={`font-display font-normal text-sm tracking-widest ${dark ? "text-sidebar-foreground/70" : "text-muted-foreground"}`}>DENTAL AI</span>
          </div>
        </Link>
        <div className="flex items-center gap-8">
          {LINKS.map((l) => {
            const active = currentSection === l.anchor;
            return (
              <a
                key={l.label}
                href={`#${l.anchor}`}
                onClick={onNav ? (e) => { e.preventDefault(); onNav(l.anchor); } : undefined}
                className={`text-sm font-medium transition-colors relative ${active ? linkActive : linkBase}`}
              >
                {l.label}
                <span className={`absolute -bottom-0.5 left-0 right-0 h-px bg-current transition-transform origin-left ${active ? "scale-x-100" : "scale-x-0"}`} />
              </a>
            );
          })}
          <Link href="/login" className={`text-sm font-medium no-underline ${linkBase}`}>Sign in</Link>
          <a
            href="#contact"
            onClick={onNav ? (e) => { e.preventDefault(); onNav("contact"); } : undefined}
            className={`text-sm font-semibold px-4 py-2 rounded-md no-underline transition-opacity ${dark ? "bg-card text-foreground hover:opacity-90" : "bg-primary text-primary-foreground hover:opacity-90"}`}
          >
            Schedule a demo
          </a>
        </div>
      </div>
    </nav>
  );
}
