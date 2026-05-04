"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { fetcher } from "@/lib/api/client";
import { Tabs } from "@/components/dental/Tabs";
import { StatusPill } from "@/components/dental/StatusPill";
import { InsurancePanel } from "../_components/InsurancePanel";
import { LifecyclePanel } from "../_components/LifecyclePanel";
import { MedicalPanel } from "../_components/MedicalPanel";
import { NotesPanel } from "../_components/NotesPanel";

const ToothChartPanel = dynamic(
  () => import("../_components/ToothChartPanel").then((m) => m.ToothChartPanel),
  { ssr: false },
);

const DocumentsPanel = dynamic(
  () => import("../_components/DocumentsPanel").then((m) => m.DocumentsPanel),
  { ssr: false },
);

interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  date_of_birth: string | null;
  status: string;
}

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "appointments", label: "Appointments" },
  { key: "denture", label: "Denture cases" },
  { key: "documents", label: "Documents" },
  { key: "tooth-chart", label: "Tooth chart" },
  { key: "notes", label: "Notes" },
  { key: "insurance", label: "Insurance" },
  { key: "medical", label: "Medical" },
  { key: "lifecycle", label: "Lifecycle" },
];

function computeAge(dob: string | null): string {
  if (!dob) return "—";
  const birth = new Date(dob);
  const now = new Date();
  const age =
    now.getFullYear() -
    birth.getFullYear() -
    (now.getMonth() < birth.getMonth() ||
    (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())
      ? 1
      : 0);
  return String(age);
}

function OverviewTab({ patient }: { patient: Patient }) {
  const { data: appointments } = useQuery({
    queryKey: ["appointments", patient.id],
    queryFn: () => fetcher<unknown[]>(`/api/appointments?patient_id=${patient.id}`),
  });
  const { data: dentureCases } = useQuery({
    queryKey: ["denture-cases", patient.id],
    queryFn: () => fetcher<unknown[]>(`/api/v2/clinical/patients/${patient.id}/denture-cases`),
  });
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-muted-foreground">DOB:</span> {patient.date_of_birth ?? "—"}</div>
        <div><span className="text-muted-foreground">Age:</span> {computeAge(patient.date_of_birth)}</div>
        <div><span className="text-muted-foreground">Phone:</span> {patient.phone ?? "—"}</div>
        <div><span className="text-muted-foreground">Email:</span> {patient.email ?? "—"}</div>
        <div className="flex items-center gap-2"><span className="text-muted-foreground">Status:</span> <StatusPill kind="patient_lifecycle" value={patient.status} /></div>
      </div>
      <div className="text-sm text-muted-foreground">
        Appointments: {Array.isArray(appointments) ? appointments.length : "…"} ·{" "}
        Open denture cases:{" "}
        {Array.isArray(dentureCases)
          ? (dentureCases as Array<{ status: string }>).filter((c) => c.status === "open").length
          : "…"}
      </div>
    </div>
  );
}

function AppointmentsTab({ patientId }: { patientId: string }) {
  const { data } = useQuery({
    queryKey: ["appointments", patientId],
    queryFn: () => fetcher<Array<{ id: string; start_time: string; status: string }>>(`/api/appointments?patient_id=${patientId}`),
  });
  return (
    <div className="space-y-2 text-sm">
      {data?.map((a) => (
        <div key={a.id} className="flex items-center gap-3 rounded border border-border px-3 py-2">
          <span>{a.start_time}</span>
          <StatusPill kind="appointment" value={a.status} />
        </div>
      ))}
      {data?.length === 0 && <p className="text-muted-foreground">No appointments.</p>}
    </div>
  );
}

function DentureCasesTab({ patientId }: { patientId: string }) {
  const { data } = useQuery({
    queryKey: ["denture-cases", patientId],
    queryFn: () => fetcher<Array<{ id: string; arch: string; case_type: string; current_stage: string; status: string }>>(`/api/v2/clinical/patients/${patientId}/denture-cases`),
  });
  return (
    <div className="space-y-2 text-sm">
      {data?.map((dc) => (
        <div key={dc.id} className="flex items-center gap-3 rounded border border-border px-3 py-2">
          <span className="font-medium">{dc.arch} / {dc.case_type}</span>
          <span className="text-muted-foreground">{dc.current_stage}</span>
          <StatusPill kind="denture_case" value={dc.status} />
        </div>
      ))}
      {data?.length === 0 && <p className="text-muted-foreground">No denture cases.</p>}
    </div>
  );
}

export default function PatientDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [activeTab, setActiveTab] = useState("overview");

  const { data: patient, isLoading } = useQuery<Patient>({
    queryKey: ["patient", id],
    queryFn: () => fetcher<Patient>(`/api/patients/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  if (!patient) return <div className="p-6 text-sm text-destructive">Patient not found.</div>;

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-foreground tracking-tight">
            {patient.first_name} {patient.last_name}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">{patient.email ?? patient.phone ?? ""}</p>
        </div>
        <StatusPill kind="patient_lifecycle" value={patient.status} />
      </div>

      <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />

      <div className="pt-2">
        {activeTab === "overview" && <OverviewTab patient={patient} />}
        {activeTab === "appointments" && <AppointmentsTab patientId={patient.id} />}
        {activeTab === "denture" && <DentureCasesTab patientId={patient.id} />}
        {activeTab === "documents" && <DocumentsPanel patientId={patient.id} />}
        {activeTab === "tooth-chart" && <ToothChartPanel patientId={patient.id} />}
        {activeTab === "notes" && <NotesPanel patientId={patient.id} />}
        {activeTab === "insurance" && <InsurancePanel patientId={patient.id} />}
        {activeTab === "medical" && <MedicalPanel patientId={patient.id} />}
        {activeTab === "lifecycle" && <LifecyclePanel patientId={patient.id} />}
      </div>
    </div>
  );
}
