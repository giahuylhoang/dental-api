"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { LoginCard } from "@/components/dental/LoginCard";
import { login } from "@/lib/auth/auth";

const LOGIN_WORDS = ["Schedules.", "Charts.", "Plans.", "Practices."];

const NODES = [
  { id: "patient", label: "Patient", x: 0.72, y: 0.14, pillar: 1 },
  { id: "chart", label: "Chart", x: 0.55, y: 0.28, pillar: 1 },
  { id: "sched", label: "Schedule", x: 0.85, y: 0.36, pillar: 1 },
  { id: "plan", label: "Plan", x: 0.65, y: 0.5, pillar: 2 },
  { id: "lab", label: "Lab", x: 0.82, y: 0.6, pillar: 2 },
  { id: "invoice", label: "Invoice", x: 0.52, y: 0.65, pillar: 2 },
  { id: "recall", label: "Recall", x: 0.7, y: 0.78, pillar: 3 },
  { id: "sms", label: "SMS · Email", x: 0.88, y: 0.82, pillar: 3 },
  { id: "insurance", label: "Insurance", x: 0.58, y: 0.42, pillar: 2 },
];

const EDGES = [
  ["patient", "chart"], ["patient", "sched"], ["chart", "plan"],
  ["chart", "insurance"], ["sched", "plan"], ["insurance", "plan"],
  ["insurance", "invoice"], ["plan", "lab"], ["plan", "recall"],
  ["invoice", "recall"], ["lab", "sms"], ["recall", "sms"],
];

const PILLAR_COLOR: Record<number, string> = { 1: "#3A7FBD", 2: "#4A90D4", 3: "#6BAED6" };

function NodeGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef<{ t: number; particles: any[]; nodes: any[] }>({ t: 0, particles: [], nodes: [] });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let raf: number;

    const init = () => {
      const W = (canvas.width = canvas.offsetWidth);
      const H = (canvas.height = canvas.offsetHeight);
      stateRef.current.nodes = NODES.map((n) => ({
        ...n, px: n.x * W, py: n.y * H, ox: n.x * W, oy: n.y * H,
        phase: Math.random() * Math.PI * 2, r: n.id === "plan" ? 7 : 5,
      }));
      const particles: any[] = [];
      EDGES.forEach(([a, b]) => {
        for (let i = 0; i < 2; i++)
          particles.push({ from: a, to: b, t: Math.random(), speed: 0.003 + Math.random() * 0.003, reverse: Math.random() > 0.5 });
      });
      stateRef.current.particles = particles;
    };

    const draw = () => {
      const W = canvas.width, H = canvas.height;
      const ctx = canvas.getContext("2d")!;
      const s = stateRef.current;
      s.t += 0.008;
      ctx.clearRect(0, 0, W, H);
      const byId: Record<string, any> = {};
      s.nodes.forEach((n) => {
        n.px = n.ox + Math.sin(s.t * 0.7 + n.phase) * 6;
        n.py = n.oy + Math.cos(s.t * 0.5 + n.phase) * 5;
        byId[n.id] = n;
      });
      EDGES.forEach(([a, b]) => {
        const na = byId[a], nb = byId[b];
        if (!na || !nb) return;
        ctx.beginPath(); ctx.moveTo(na.px, na.py); ctx.lineTo(nb.px, nb.py);
        ctx.strokeStyle = "rgba(58,127,189,0.18)"; ctx.lineWidth = 1; ctx.stroke();
      });
      s.particles.forEach((p) => {
        p.t += p.speed * (p.reverse ? -1 : 1);
        if (p.t > 1) p.t = 0; if (p.t < 0) p.t = 1;
        const na = byId[p.from], nb = byId[p.to];
        if (!na || !nb) return;
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
    const ro = new ResizeObserver(() => init());
    ro.observe(canvas);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); };
  }, []);

  return <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />;
}

export default function LoginPage() {
  const router = useRouter();
  const [wordIdx, setWordIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => { setWordIdx((i) => (i + 1) % LOGIN_WORDS.length); setVisible(true); }, 380);
    }, 2800);
    return () => clearInterval(id);
  }, []);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    await login({ email: fd.get("email") as string, password: fd.get("password") as string });
    router.push("/dashboard");
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.05fr 1fr", minHeight: "100vh", position: "relative", overflow: "hidden", background: "#060F1E", color: "var(--rr-warm-white)" }}>
      {/* Left column */}
      <div style={{ padding: "60px 56px", display: "flex", flexDirection: "column", justifyContent: "space-between", position: "relative", zIndex: 2 }}>
        <a href="/" style={{ display: "flex", alignItems: "center", gap: 12, textDecoration: "none" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/assets/RR_logo_white.svg" alt="Rockyridge Dental AI" style={{ height: 32 }} />
          <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.05 }}>
            <span style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: "0.95rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--rr-warm-white)" }}>ROCKYRIDGE</span>
            <span style={{ fontFamily: "var(--font-display)", fontWeight: 400, fontSize: "0.82rem", letterSpacing: "1.8px", color: "rgba(250,249,246,0.7)", textTransform: "uppercase" }}>DENTAL AI</span>
          </div>
        </a>

        <div style={{ maxWidth: 540 }}>
          <div style={{ fontFamily: "var(--font-ui)", fontWeight: 600, fontSize: "0.72rem", letterSpacing: "0.15em", textTransform: "uppercase", color: "#6BAED6", marginBottom: 24 }}>
            Sign in to your workspace · Sovereign · Audit-logged
          </div>
          <h1 style={{ fontFamily: "var(--font-display)", fontWeight: 900, fontSize: "clamp(2.2rem, 4.5vw, 3.6rem)", lineHeight: 1.08, letterSpacing: "-0.03em", color: "var(--rr-warm-white)", margin: 0 }}>
            Architecting<br />Sovereign{" "}
            <span style={{
              display: "inline-block", color: "#6BAED6", minWidth: "4ch",
              opacity: visible ? 1 : 0,
              transform: visible ? "translateY(0)" : "translateY(10px)",
              transition: "opacity 320ms cubic-bezier(0.16,1,0.3,1), transform 320ms cubic-bezier(0.16,1,0.3,1)",
            }}>
              {LOGIN_WORDS[wordIdx]}
            </span>
          </h1>
          <p style={{ fontFamily: "var(--font-ui)", fontSize: "1rem", lineHeight: 1.75, color: "rgba(250,249,246,0.6)", marginTop: 22, maxWidth: 460 }}>
            Open the schedule. Open the chart. Open the lab. The history is already there — patient context, recall windows, lab ETAs, insurance status, all in one connected system.
          </p>
        </div>

        <div style={{ display: "flex", gap: 36, paddingTop: 32, borderTop: "1px solid rgba(255,255,255,0.09)", flexWrap: "wrap" }}>
          {[
            ["Sovereign", "Your data, your tenancy"],
            ["Audit-logged", "Every clinical edit, every login"],
            ["Light-on-the-eyes", "8-hour shift-friendly"],
          ].map(([k, v]) => (
            <div key={k}>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1rem", color: "var(--rr-warm-white)", letterSpacing: "-0.01em" }}>{k}</div>
              <div style={{ fontFamily: "var(--font-ui)", fontSize: "0.72rem", color: "rgba(250,249,246,0.4)", marginTop: 3, letterSpacing: "0.03em" }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right column */}
      <div style={{ position: "relative", height: "100vh" }}>
        {[["THE SCHEDULE", "14%"], ["THE CHART", "47%"], ["THE LAB", "76%"]].map(([lbl, top]) => (
          <div key={lbl} style={{
            position: "absolute", left: 8, top,
            fontFamily: "var(--font-ui)", fontWeight: 700, fontSize: "0.6rem",
            letterSpacing: "0.14em", textTransform: "uppercase",
            color: "rgba(58,127,189,0.35)", writingMode: "vertical-rl",
            transform: "rotate(180deg)", userSelect: "none",
          }}>{lbl}</div>
        ))}
        {["33.3%", "66.6%"].map((top) => (
          <div key={top} style={{ position: "absolute", left: 32, right: 0, top, height: 1, background: "rgba(58,127,189,0.07)" }} />
        ))}
        <div style={{ position: "absolute", inset: 0, opacity: 0.85 }}>
          <NodeGraph />
        </div>
      </div>

      {/* Login card overlay */}
      <div style={{ position: "absolute", right: 56, top: "50%", transform: "translateY(-50%)", zIndex: 3 }}>
        <LoginCard onSubmit={handleSubmit} />
      </div>
    </div>
  );
}
