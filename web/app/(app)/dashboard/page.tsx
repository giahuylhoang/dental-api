"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetcher } from "@/lib/api/client";
import { useAuthStore } from "@/lib/auth/store";
import { KpiTile } from "@/components/dental/KpiTile";
import { AppointmentCard, type Appointment } from "@/components/dental/AppointmentCard";
import { LabPipeline } from "@/components/dental/LabPipeline";
import { ToothChartTile } from "@/components/dental/ToothChartTile";
import { PatientCard, type Patient } from "@/components/dental/PatientCard";
import styles from "./page.module.css";

// Seed data for sections without implemented endpoints
// TODO: wire to dental-agent — endpoint not yet implemented
const SEED_APPOINTMENTS: Appointment[] = [
  { id: "A-1", time: "08:30", duration: 30, patient: "Alice Stevens",  provider: "Dr Hau Le",   chair: "1", kind: "Recall · 6mo",           status: "confirmed" },
  { id: "A-2", time: "09:00", duration: 60, patient: "Priya Khanna",   provider: "Dr Hau Le",   chair: "1", kind: "Crown prep · #36",       status: "confirmed" },
  { id: "A-3", time: "09:30", duration: 45, patient: "Marcus Doan",    provider: "Dr Sara Lim", chair: "2", kind: "Denture relines · upper", status: "pending"   },
  { id: "A-4", time: "10:30", duration: 30, patient: "Eli Brouwer",    provider: "Hyg. Renu",   chair: "3", kind: "Hygiene · scaling",      status: "confirmed" },
  { id: "A-5", time: "11:00", duration: 90, patient: "Sofía Castillo", provider: "Dr Sara Lim", chair: "2", kind: "Implant follow-up",      status: "confirmed" },
  { id: "A-6", time: "13:00", duration: 60, patient: "Alice Stevens",  provider: "Dr Hau Le",   chair: "1", kind: "Composite · MOD #14",    status: "no_show"   },
  { id: "A-7", time: "14:30", duration: 30, patient: "Daniel Okafor",  provider: "Hyg. Renu",   chair: "3", kind: "New patient consult",    status: "pending"   },
  { id: "A-8", time: "15:30", duration: 45, patient: "Priya Khanna",   provider: "Dr Hau Le",   chair: "1", kind: "Crown seat · #36",       status: "confirmed" },
];

const SEED_PATIENTS: Patient[] = [
  { id: "P-018342", first: "Alice",  last: "Stevens",  dob: "1984-03-12", insurance: "Alberta Blue Cross", status: "active"   },
  { id: "P-018298", first: "Marcus", last: "Doan",     dob: "1971-09-04", insurance: "Sun Life",           status: "recall"   },
  { id: "P-018501", first: "Priya",  last: "Khanna",   dob: "1992-06-29", insurance: "Manulife",           status: "active"   },
  { id: "P-017901", first: "Eli",    last: "Brouwer",  dob: "2003-01-17", insurance: "Canada Life",        status: "plan"     },
  { id: "P-018611", first: "Sofía",  last: "Castillo", dob: "1956-11-22", insurance: "Alberta Health",     status: "active"   },
  { id: "P-016102", first: "Daniel", last: "Okafor",   dob: "1988-07-08", insurance: "Pacific Blue Cross", status: "inactive" },
];

interface KpiData {
  schedule_fill?: number;
  recall_reach?: number;
  no_shows?: number;
  lab_in_flight?: number;
}

interface Invoice {
  id: string;
  patient: string;
  total: number;
  balance: number;
  status: "paid" | "partial" | "unpaid";
}

export default function DashboardPage() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const [expandedApptId, setExpandedApptId] = useState<string | null>(null);

  const { data: kpi } = useQuery<KpiData>({
    queryKey: ["reporting", "kpi", clinicId],
    queryFn: () => fetcher<KpiData>("/api/v2/reporting/kpi"),
  });

  const { data: invoices = [] } = useQuery<Invoice[]>({
    queryKey: ["invoices", "recent", clinicId],
    queryFn: () => fetcher<Invoice[]>("/api/v2/billing/invoices?limit=5"),
  });

  const scheduleFill = kpi?.schedule_fill != null ? `${kpi.schedule_fill}%` : "78%";
  const recallReach  = kpi?.recall_reach  != null ? `${kpi.recall_reach}%`  : "92%";
  const noShows      = kpi?.no_shows      != null ? String(kpi.no_shows)     : "3";
  const labInFlight  = kpi?.lab_in_flight != null ? String(kpi.lab_in_flight): "5";

  // Use seed invoices if API returns empty
  const displayInvoices: Invoice[] = invoices.length > 0 ? invoices : [
    { id: "INV-2026-0871", patient: "Alice Stevens",  total: 480.00,   balance:    0.00, status: "paid"    },
    { id: "INV-2026-0870", patient: "Priya Khanna",   total: 1240.00,  balance:  620.00, status: "partial" },
    { id: "INV-2026-0869", patient: "Sofía Castillo", total: 2180.50,  balance: 2180.50, status: "unpaid"  },
    { id: "INV-2026-0868", patient: "Marcus Doan",    total:  220.00,  balance:    0.00, status: "paid"    },
  ];

  return (
    <div className={styles.body}>
      {/* Page header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Today&apos;s clinic</h1>
          <div className={styles.pageSub}>Saturday · May 4 · 2026 — 8 appointments scheduled · 5 lab cases in flight.</div>
        </div>
        <div className={styles.headerActions}>
          <button className="btn btn-ghost btn-md">Export day</button>
          <button className="btn btn-primary btn-md">+ New appointment</button>
        </div>
      </div>

      {/* 4-column KPI strip */}
      <div className={styles.kpiRow}>
        <KpiTile label="Schedule fill" value={scheduleFill} delta="+ 4%"   trend="up"   accent="steel" />
        <KpiTile label="Recall reach"  value={recallReach}  delta="+ 1.2%" trend="up"   accent="steel" />
        <KpiTile label="No-shows"      value={noShows}      delta="+ 1"    trend="down" accent="navy"  />
        <KpiTile label="Lab in flight" value={labInFlight}  delta="– 2"    trend="up"   accent="steel" />
      </div>

      {/* Main 2-col grid: appointments + side panel */}
      <div className={styles.grid2}>
        {/* Today's appointments panel */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <div className={styles.panelHTitle}>Today&apos;s appointments</div>
              <div className={styles.panelHSub}>8 scheduled · 6 confirmed · 1 pending · 1 no-show</div>
            </div>
            <a className={styles.panelHAction} href="/schedule">Open the schedule →</a>
          </div>
          <div className={styles.stack}>
            {SEED_APPOINTMENTS.map((a) => (
              <div key={a.id}>
                <AppointmentCard
                  appointment={a}
                  expanded={expandedApptId === a.id}
                  onClick={() => setExpandedApptId(expandedApptId === a.id ? null : a.id)}
                />
                {expandedApptId === a.id && (
                  <div className={styles.apptQuickActions}>
                    <button className="btn btn-ghost btn-md">Check in</button>
                    <button className="btn btn-primary btn-md">Open Chart</button>
                    <button className="btn btn-ghost btn-md">Reschedule</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Side panel: Lab pipeline + Tooth chart */}
        <div className={styles.sideCol}>
          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <div className={styles.panelHTitle}>Lab pipeline</div>
                <div className={styles.panelHSub}>Sent · in progress · returned</div>
              </div>
              <a className={styles.panelHAction} href="/lab">Open the lab →</a>
            </div>
            <LabPipeline />
          </div>
          <ToothChartTile />
        </div>
      </div>

      {/* Recent patients */}
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <div className={styles.panelHTitle}>Recent patients</div>
            <div className={styles.panelHSub}>Last 6 visits across all providers</div>
          </div>
          <a className={styles.panelHAction} href="/patients">All patients →</a>
        </div>
        <div className={styles.stack} style={{ gap: 8 }}>
          {SEED_PATIENTS.map((p) => (
            <PatientCard key={p.id} patient={p} />
          ))}
        </div>
      </div>

      {/* Recent invoices */}
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <div className={styles.panelHTitle}>Recent invoices</div>
            <div className={styles.panelHSub}>Last 4 days</div>
          </div>
          <a className={styles.panelHAction} href="/billing">All invoices →</a>
        </div>
        <table className={styles.recentTable}>
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Patient</th>
              <th style={{ textAlign: "right" }}>Total</th>
              <th style={{ textAlign: "right" }}>Balance</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {displayInvoices.map((i) => (
              <tr key={i.id}>
                <td className={styles.id}>{i.id}</td>
                <td>{i.patient}</td>
                <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>${i.total.toFixed(2)}</td>
                <td style={{ textAlign: "right", fontFamily: "var(--font-mono)", color: i.balance > 0 ? "#B45309" : "#4A5568" }}>${i.balance.toFixed(2)}</td>
                <td>
                  <span style={{
                    fontSize: ".66rem", fontWeight: 600, padding: "3px 10px", borderRadius: 4,
                    letterSpacing: ".06em", textTransform: "uppercase",
                    background: i.status === "paid" ? "#E8F5EE" : i.status === "partial" ? "#FDF3E5" : "#F8E5E8",
                    color:      i.status === "paid" ? "#2A7D4F" : i.status === "partial" ? "#B45309" : "#9B2335",
                  }}>{i.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className={styles.footer}>ROCKYRIDGE · DENTAL AI · v1</div>
    </div>
  );
}
