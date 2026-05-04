import React from "react";
import { Calendar, ClipboardList, FlaskConical } from "lucide-react";

const PILLARS = [
  {
    number: "01", label: "The Schedule",
    title: "Operatory at a glance",
    desc: "Real-time chair-by-chair availability across operatories, providers, and recall windows. Drag to reschedule with automated patient SMS — conflicts flagged before save.",
    items: ["Per-clinic working hours · holidays · rotations", "Drag-to-reschedule with SMS reminders", "Recall windows surfaced before they go stale", "Sovereign export to ICS / CSV / your PMS"],
    icon: <Calendar className="w-7 h-7" />,
  },
  {
    number: "02", label: "The Chart",
    title: "One screen, always in sync",
    desc: "Tooth-level history, treatment plans, lab cases, insurance, and clinical notes — never duplicated across systems, never out of sync. Open a chart, and the history is already there.",
    items: ["Tooth-level history · 32-tooth chart", "Treatment plans · accepted, in-flight, completed", "Insurance verification · claim auto-submission", "Audit log on every clinical edit"],
    icon: <ClipboardList className="w-7 h-7" />,
  },
  {
    number: "03", label: "The Lab",
    title: "Every case, end to end",
    desc: "Track lab cases from impression to seat. Vendor SLAs, materials, lot numbers, and patient ETAs — all in one queue with status changes broadcast to the clinical chart.",
    items: ["Vendor SLAs · materials · lot tracking", "Status broadcast to chair-side chart", "Patient ETA on the appointment", "Late-case alerts surfaced in the schedule"],
    icon: <FlaskConical className="w-7 h-7" />,
  },
];

export function Pillars() {
  return (
    <section id="services" className="bg-background py-24 px-12">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16 max-w-xl">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary mb-4">The Three-Pillar System</div>
          <h2 className="font-display font-bold text-4xl tracking-tight text-foreground">Schedule · Chart · Lab</h2>
          <p className="text-base leading-loose text-muted-foreground mt-4 max-w-lg">
            Three pillars, one connected system. Patient histories never duplicate. Lab cases never go stale. Insurance never gets dropped.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-6">
          {PILLARS.map((p, i) => (
            <div
              key={p.number}
              className={`rounded-md p-9 flex flex-col gap-5 ${
                i === 1 ? "bg-sidebar shadow-2xl" : "bg-card border border-border shadow-sm"
              }`}
            >
              <div className="flex justify-between items-start">
                <span className={`font-display font-black text-5xl leading-none tracking-tight ${i === 1 ? "text-white/10" : "text-foreground/10"}`}>{p.number}</span>
                <span className="text-primary mt-1">{p.icon}</span>
              </div>
              <div className={`text-xs font-semibold uppercase tracking-widest ${i === 1 ? "text-muted-foreground" : "text-primary"}`}>{p.label}</div>
              <div className={`font-display font-bold text-xl tracking-tight leading-snug ${i === 1 ? "text-sidebar-foreground" : "text-foreground"}`}>{p.title}</div>
              <p className={`text-sm leading-relaxed ${i === 1 ? "text-sidebar-foreground/60" : "text-muted-foreground"}`}>{p.desc}</p>
              <div className={`h-px ${i === 1 ? "bg-white/10" : "bg-border"}`} />
              <ul className="list-none p-0 m-0 flex flex-col gap-2">
                {p.items.map((item) => (
                  <li key={item} className={`flex items-center gap-2.5 text-sm ${i === 1 ? "text-sidebar-foreground/70" : "text-muted-foreground"}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />{item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
