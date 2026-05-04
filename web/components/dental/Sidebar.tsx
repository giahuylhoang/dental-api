"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import {
  LayoutGrid, Users, Calendar, ClipboardList, FlaskConical,
  DollarSign, MessageSquare, UserPlus, BarChart3, Settings,
  ChevronDown, Mic,
} from "lucide-react";

const NAV = [
  { key: "dashboard",       label: "Dashboard",       href: "/dashboard",       group: "Care",       icon: LayoutGrid },
  { key: "patients",        label: "Patients",         href: "/patients",        group: "Care",       icon: Users },
  { key: "schedule",        label: "Schedule",         href: "/schedule",        group: "Care",       icon: Calendar },
  { key: "plans",           label: "Treatment",        href: "/plans",           group: "Care",       icon: ClipboardList },
  { key: "lab",             label: "Lab",              href: "/lab",             group: "Care",       icon: FlaskConical },
  { key: "billing",         label: "Billing",          href: "/billing",         group: "Operations", icon: DollarSign },
  { key: "communications",  label: "Communications",   href: "/communications",  group: "Operations", icon: MessageSquare },
  { key: "crm",             label: "CRM",              href: "/crm",             group: "Operations", icon: UserPlus },
  { key: "reports",         label: "Reports",          href: "/reports",         group: "Insights",   icon: BarChart3 },
  { key: "settings",        label: "Settings",         href: "/settings",        group: "System",     icon: Settings },
  { key: "ai-receptionist", label: "AI Receptionist",  href: "/login",           group: "Operations", icon: Mic, isNew: true },
];

const GROUP_ORDER = ["Care", "Operations", "Insights", "System"];

export interface SidebarProps {
  collapsed?: boolean;
  clinicName?: string;
  userName?: string;
  onNav?: (key: string) => void;
}

export function Sidebar({ collapsed = false, clinicName = "Oak Dental Calgary", userName = "Dr Hau Le", onNav }: SidebarProps) {
  const pathname = usePathname();
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const groups = GROUP_ORDER.map((g) => ({ label: g, items: NAV.filter((n) => n.group === g) }));
  const initials = userName.split(" ").map((s) => s[0]).slice(0, 2).join("");

  return (
    <aside className={`${collapsed ? "w-16" : "w-60"} min-h-screen bg-sidebar text-sidebar-foreground flex flex-col shrink-0 transition-all duration-300 sticky top-0`}>
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-white/10">
        <div className="w-7 h-7 rounded bg-primary shrink-0" />
        {!collapsed && (
          <div className="flex flex-col leading-tight">
            <span className="font-display font-extrabold text-xs tracking-widest uppercase">ROCKYRIDGE</span>
            <span className="font-display font-normal text-xs text-sidebar-foreground/60 tracking-widest uppercase">DENTAL AI</span>
          </div>
        )}
      </div>

      {/* Clinic switcher */}
      {!collapsed && (
        <div className="px-3 pt-3 pb-1 relative">
          <button
            type="button"
            aria-expanded={switcherOpen}
            onClick={() => setSwitcherOpen((o) => !o)}
            className="w-full flex items-center justify-between bg-primary/10 border border-white/15 rounded-md px-3 py-2.5 text-sidebar-foreground text-sm font-medium cursor-pointer text-left"
          >
            <span className="truncate">{clinicName}</span>
            <ChevronDown className={`w-3.5 h-3.5 shrink-0 transition-transform ${switcherOpen ? "rotate-180" : ""}`} />
          </button>
        </div>
      )}

      {/* Nav */}
      <div className="flex-1 overflow-y-auto">
        {groups.map((g) => (
          <div key={g.label} className="px-2.5 pt-4 pb-1">
            {!collapsed && (
              <div className="text-xs font-semibold uppercase tracking-widest text-sidebar-foreground/50 px-2.5 pb-1">{g.label}</div>
            )}
            {g.items.map((it) => {
              const isActive = pathname === it.href || pathname.startsWith(it.href + "/");
              const Icon = it.icon;
              return (
                <Link
                  key={it.key}
                  href={it.href}
                  aria-current={isActive ? "page" : undefined}
                  title={collapsed ? it.label : undefined}
                  onClick={onNav ? (e) => { e.preventDefault(); onNav(it.key); } : undefined}
                  className={`flex items-center gap-2.5 rounded px-2.5 py-2 text-sm transition-colors no-underline mb-0.5 ${
                    collapsed ? "justify-center" : ""
                  } ${isActive ? "bg-primary text-primary-foreground font-semibold" : "text-sidebar-foreground/75 hover:bg-white/10 font-normal"}`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {!collapsed && (
                    <>
                      {it.label}
                      {"isNew" in it && it.isNew && (
                        <span className="ml-1.5 text-xs font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-primary text-primary-foreground">NEW</span>
                      )}
                    </>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* User footer */}
      <div className="px-3.5 py-3.5 border-t border-white/10 flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center font-semibold text-xs text-primary-foreground shrink-0">
          {initials}
        </div>
        {!collapsed && (
          <div className="flex flex-col leading-snug">
            <span className="text-sm">{userName}</span>
            <span className="text-xs text-sidebar-foreground/50">{clinicName}</span>
          </div>
        )}
      </div>
    </aside>
  );
}
