"use client";

import React, { useEffect, useRef, useState } from "react";

const CYCLE_WORDS = ["Schedules.", "Charts.", "Plans.", "Practices."];

const NODES = [
  { id: "patient",   label: "Patient",     x: 0.72, y: 0.14, pillar: 1 },
  { id: "chart",     label: "Chart",       x: 0.55, y: 0.28, pillar: 1 },
  { id: "sched",     label: "Schedule",    x: 0.85, y: 0.36, pillar: 1 },
  { id: "plan",      label: "Plan",        x: 0.65, y: 0.50, pillar: 2 },
  { id: "lab",       label: "Lab",         x: 0.82, y: 0.60, pillar: 2 },
  { id: "invoice",   label: "Invoice",     x: 0.52, y: 0.65, pillar: 2 },
  { id: "recall",    label: "Recall",      x: 0.70, y: 0.78, pillar: 3 },
  { id: "sms",       label: "SMS · Email", x: 0.88, y: 0.82, pillar: 3 },
  { id: "insurance", label: "Insurance",   x: 0.58, y: 0.42, pillar: 2 },
];

const EDGES: [string, string][] = [
  ["patient","chart"], ["patient","sched"], ["chart","plan"], ["chart","insurance"],
  ["sched","plan"], ["insurance","plan"], ["insurance","invoice"], ["plan","lab"],
  ["plan","recall"], ["invoice","recall"], ["lab","sms"], ["recall","sms"],
];

const PILLAR_COLOR: Record<number, string> = { 1: "rgb(58,127,189)", 2: "rgb(74,144,212)", 3: "rgb(107,174,214)" };

interface NodeState {
  id: string; label: string; x: number; y: number; pillar: number;
  px: number; py: number; ox: number; oy: number; phase: number; r: number;
}
interface Particle { from: string; to: string; t: number; speed: number; reverse: boolean; }

function NodeGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef<{ t: number; particles: Particle[]; nodes: NodeState[] }>({ t: 0, particles: [], nodes: [] });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let raf: number;

    const init = () => {
      const W = canvas.width = canvas.offsetWidth;
      const H = canvas.height = canvas.offsetHeight;
      stateRef.current.nodes = NODES.map((n) => ({
        ...n, px: n.x * W, py: n.y * H, ox: n.x * W, oy: n.y * H,
        phase: Math.random() * Math.PI * 2, r: n.id === "plan" ? 7 : 5,
      }));
      const particles: Particle[] = [];
      EDGES.forEach(([a, b]) => {
        for (let i = 0; i < 2; i++)
          particles.push({ from: a, to: b, t: Math.random(), speed: 0.003 + Math.random() * 0.003, reverse: Math.random() > 0.5 });
      });
      stateRef.current.particles = particles;
    };

    const draw = () => {
      const W = canvas.width, H = canvas.height;
      const ctx = canvas.getContext("2d")!;
      const s = stateRef.current; s.t += 0.008;
      ctx.clearRect(0, 0, W, H);
      const byId: Record<string, NodeState> = {};
      s.nodes.forEach((n) => {
        n.px = n.ox + Math.sin(s.t * 0.7 + n.phase) * 6;
        n.py = n.oy + Math.cos(s.t * 0.5 + n.phase) * 5;
        byId[n.id] = n;
      });
      EDGES.forEach(([a, b]) => {
        const na = byId[a], nb = byId[b]; if (!na || !nb) return;
        ctx.beginPath(); ctx.moveTo(na.px, na.py); ctx.lineTo(nb.px, nb.py);
        ctx.strokeStyle = "rgba(58,127,189,0.18)"; ctx.lineWidth = 1; ctx.stroke();
      });
      s.particles.forEach((p) => {
        p.t += p.speed * (p.reverse ? -1 : 1);
        if (p.t > 1) p.t = 0; if (p.t < 0) p.t = 1;
        const na = byId[p.from], nb = byId[p.to]; if (!na || !nb) return;
        const x = na.px + (nb.px - na.px) * p.t, y = na.py + (nb.py - na.py) * p.t;
        ctx.beginPath(); ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(107,174,214,0.85)"; ctx.fill();
      });
      s.nodes.forEach((n) => {
        const col = PILLAR_COLOR[n.pillar];
        if (n.id === "plan") {
          const pulse = 0.4 + 0.3 * Math.sin(s.t * 2);
          ctx.beginPath(); ctx.arc(n.px, n.py, 18, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(58,127,189,${pulse})`; ctx.lineWidth = 1; ctx.stroke();
        }
        ctx.beginPath(); ctx.arc(n.px, n.py, n.r, 0, Math.PI * 2);
        ctx.fillStyle = col; ctx.fill();
        ctx.beginPath(); ctx.arc(n.px, n.py, n.r * 0.45, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(10,25,47,0.5)"; ctx.fill();
        ctx.font = "500 10px Inter, sans-serif";
        ctx.fillStyle = "rgba(250,249,246,0.55)";
        ctx.textAlign = "center"; ctx.fillText(n.label, n.px, n.py + n.r + 13);
      });
      raf = requestAnimationFrame(draw);
    };

    init(); draw();
    const ro = new ResizeObserver(() => init()); ro.observe(canvas);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); };
  }, []);

  return <canvas ref={canvasRef} className="w-full h-full block" />;
}

export interface HeroProps {
  onNav?: (anchor: string) => void;
}

export function Hero({ onNav }: HeroProps) {
  const [wordIdx, setWordIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => { setWordIdx((i) => (i + 1) % CYCLE_WORDS.length); setVisible(true); }, 380);
    }, 2800);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="bg-sidebar min-h-screen grid grid-cols-2 items-center py-24 relative overflow-hidden">
      <div className="px-12 max-w-xl">
        <div className="text-xs font-semibold uppercase tracking-widest text-primary mb-6">
          Rockyridge Dental AI · Systems Thinking for Practice Operations
        </div>
        <h1 className="font-display font-black text-5xl leading-tight tracking-tight text-sidebar-foreground">
          Architecting<br />Sovereign{" "}
          <span className={`inline-block text-blue-300 transition-all duration-300 min-w-[4ch] ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2.5"}`}>
            {CYCLE_WORDS[wordIdx]}
          </span>
        </h1>
        <p className="text-base leading-loose text-sidebar-foreground/60 mt-6 max-w-md">
          The dental practice OS for clinics that want their schedule, their charts, their lab cases, and their insurance reconciliation — all in one place, owned by the clinic.
        </p>
        <div className="flex gap-4 mt-10 flex-wrap items-center">
          <button onClick={() => onNav?.("contact")} className="bg-card text-foreground rounded-md px-5 py-2.5 text-sm font-semibold hover:opacity-90 transition-opacity">
            Schedule a demo
          </button>
          <button onClick={() => onNav?.("services")} className="bg-card text-foreground rounded-md px-5 py-2.5 text-sm font-semibold opacity-60 hover:opacity-80 transition-opacity">
            See it work
          </button>
        </div>
        <div className="flex gap-10 mt-16 pt-9 border-t border-white/10 flex-wrap">
          {[["Three Pillars","Schedule · Chart · Lab"], ["Sovereign","Your data, your servers"], ["Audit-logged","Always · forever"]].map(([s, d]) => (
            <div key={s}>
              <div className="font-display font-bold text-base text-sidebar-foreground">{s}</div>
              <div className="text-xs text-sidebar-foreground/40 mt-0.5 tracking-wide">{d}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="h-screen relative opacity-90">
        <div className="absolute left-2 top-[14%] font-bold text-xs tracking-widest uppercase text-primary/35 select-none [writing-mode:vertical-rl] rotate-180">THE SCHEDULE</div>
        <div className="absolute left-2 top-[47%] font-bold text-xs tracking-widest uppercase text-primary/35 select-none [writing-mode:vertical-rl] rotate-180">THE CHART</div>
        <div className="absolute left-2 top-[76%] font-bold text-xs tracking-widest uppercase text-primary/35 select-none [writing-mode:vertical-rl] rotate-180">THE LAB</div>
        <NodeGraph />
      </div>
    </section>
  );
}
