import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import LifecyclePanel from './LifecyclePanel';
import MedicalForm from './MedicalForm';
import InsuranceList from './InsuranceList';
import DocumentUploader from './DocumentUploader';
import DocumentList from './DocumentList';
import ToothChart from './ToothChart';
import NotesPanel from './NotesPanel';

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
  'Overview',
  'Status',
  'Medical',
  'Insurance',
  'Documents',
  'Tooth Chart',
  'Treatment Plans',
  'Denture Cases',
  'Notes',
  'Appointments',
  'Invoices',
  'Communications',
] as const;

type Tab = (typeof TABS)[number];

const TAB_PARAM: Record<Tab, string> = {
  Overview: 'overview',
  Status: 'status',
  Medical: 'medical',
  Insurance: 'insurance',
  Documents: 'documents',
  'Tooth Chart': 'tooth-chart',
  'Treatment Plans': 'treatment-plans',
  'Denture Cases': 'denture-cases',
  Notes: 'notes',
  Appointments: 'appointments',
  Invoices: 'invoices',
  Communications: 'communications',
};

const PARAM_TO_TAB: Record<string, Tab> = Object.fromEntries(
  Object.entries(TAB_PARAM).map(([k, v]) => [v, k as Tab]),
);

function computeAge(dob: string | null): string {
  if (!dob) return '—';
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
    queryKey: ['appointments', patient.id],
    queryFn: () => fetcher<unknown[]>(`/api/appointments?patient_id=${patient.id}`),
  });
  const { data: dentureCases } = useQuery({
    queryKey: ['denture-cases', patient.id],
    queryFn: () =>
      fetcher<unknown[]>(`/api/v2/clinical/patients/${patient.id}/denture-cases`),
  });
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-zinc-500">DOB:</span> {patient.date_of_birth ?? '—'}
        </div>
        <div>
          <span className="text-zinc-500">Age:</span> {computeAge(patient.date_of_birth)}
        </div>
        <div>
          <span className="text-zinc-500">Phone:</span> {patient.phone ?? '—'}
        </div>
        <div>
          <span className="text-zinc-500">Email:</span> {patient.email ?? '—'}
        </div>
        <div>
          <span className="text-zinc-500">Status:</span> {patient.status}
        </div>
      </div>
      <div className="text-sm text-zinc-500">
        Appointments: {Array.isArray(appointments) ? appointments.length : '…'} |{' '}
        Open denture cases:{' '}
        {Array.isArray(dentureCases)
          ? (dentureCases as Array<{ status: string }>).filter((c) => c.status === 'open').length
          : '…'}
      </div>
    </div>
  );
}

function TreatmentPlansTab({ patientId }: { patientId: string }) {
  const { data } = useQuery({
    queryKey: ['treatment-plans', patientId],
    queryFn: () =>
      fetcher<Array<{ id: string; status: string; total_estimate: number }>>(
        `/api/v2/clinical/patients/${patientId}/treatment-plans`,
      ),
  });
  return (
    <div className="space-y-2 text-sm">
      {data?.map((tp) => (
        <div
          key={tp.id}
          className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2"
        >
          <span>Plan #{tp.id}</span>
          <span className="text-zinc-500">{tp.status}</span>
          <span>${tp.total_estimate.toFixed(2)}</span>
        </div>
      ))}
      {data?.length === 0 && <p className="text-zinc-500">No treatment plans.</p>}
    </div>
  );
}

function DentureCasesTab({ patientId }: { patientId: string }) {
  const { data } = useQuery({
    queryKey: ['denture-cases', patientId],
    queryFn: () =>
      fetcher<
        Array<{
          id: string;
          arch: string;
          case_type: string;
          current_stage: string;
          status: string;
        }>
      >(`/api/v2/clinical/patients/${patientId}/denture-cases`),
  });
  return (
    <div className="space-y-2 text-sm">
      {data?.map((dc) => (
        <div
          key={dc.id}
          className="flex items-center gap-3 rounded border border-zinc-200 px-3 py-2"
        >
          <span className="font-medium">
            {dc.arch} / {dc.case_type}
          </span>
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
            {dc.current_stage}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs ${dc.status === 'open' ? 'bg-green-100 text-green-700' : 'bg-zinc-100 text-zinc-600'}`}
          >
            {dc.status}
          </span>
        </div>
      ))}
      {data?.length === 0 && <p className="text-zinc-500">No denture cases.</p>}
    </div>
  );
}

function AppointmentsTab({ patientId }: { patientId: string }) {
  const { data } = useQuery({
    queryKey: ['appointments', patientId],
    queryFn: () =>
      fetcher<Array<{ id: string; start_time: string; status: string }>>(
        `/api/appointments?patient_id=${patientId}`,
      ),
  });
  return (
    <div className="space-y-2 text-sm">
      {data?.map((a) => (
        <div
          key={a.id}
          className="flex items-center gap-3 rounded border border-zinc-200 px-3 py-2"
        >
          <span>{a.start_time}</span>
          <span className="text-zinc-500">{a.status}</span>
        </div>
      ))}
      {data?.length === 0 && <p className="text-zinc-500">No appointments.</p>}
    </div>
  );
}

function InvoicesTab({ patientId }: { patientId: string }) {
  return (
    <div className="text-sm text-zinc-500">
      Invoices for patient {patientId} — Track 5 owns the editor.
    </div>
  );
}

function CommunicationsTab({ patientId }: { patientId: string }) {
  return (
    <div className="text-sm text-zinc-500">
      Communications for patient {patientId} — Track 5 owns send.
    </div>
  );
}

export default function Patient360() {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabParam = searchParams.get('tab') ?? 'overview';
  const activeTab: Tab = PARAM_TO_TAB[tabParam] ?? 'Overview';

  function setTab(tab: Tab) {
    setSearchParams({ tab: TAB_PARAM[tab] }, { replace: true });
  }

  const { data: patient, isLoading } = useQuery<Patient>({
    queryKey: ['patient', id],
    queryFn: () => fetcher<Patient>(`/api/patients/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;
  if (!patient) return <p className="text-sm text-red-600">Patient not found.</p>;

  return (
    <div>
      <div className="mb-4">
        <h2 className="text-xl font-semibold">
          {patient.first_name} {patient.last_name}
        </h2>
        <p className="text-sm text-zinc-500">
          {patient.email} · {patient.phone}
        </p>
      </div>

      <div className="mb-4 flex flex-wrap gap-1 border-b border-zinc-200">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setTab(tab)}
            className={`px-3 py-2 text-sm font-medium ${
              activeTab === tab
                ? 'border-b-2 border-zinc-900 text-zinc-900'
                : 'text-zinc-500 hover:text-zinc-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div>
        {activeTab === 'Overview' && <OverviewTab patient={patient} />}
        {activeTab === 'Status' && <LifecyclePanel patientId={patient.id} />}
        {activeTab === 'Medical' && <MedicalForm patientId={patient.id} />}
        {activeTab === 'Insurance' && <InsuranceList patientId={patient.id} />}
        {activeTab === 'Documents' && (
          <div className="space-y-6">
            <DocumentUploader patientId={patient.id} />
            <DocumentList patientId={patient.id} />
          </div>
        )}
        {activeTab === 'Tooth Chart' && <ToothChart patientId={patient.id} />}
        {activeTab === 'Treatment Plans' && <TreatmentPlansTab patientId={patient.id} />}
        {activeTab === 'Denture Cases' && <DentureCasesTab patientId={patient.id} />}
        {activeTab === 'Notes' && <NotesPanel patientId={patient.id} />}
        {activeTab === 'Appointments' && <AppointmentsTab patientId={patient.id} />}
        {activeTab === 'Invoices' && <InvoicesTab patientId={patient.id} />}
        {activeTab === 'Communications' && <CommunicationsTab patientId={patient.id} />}
      </div>
    </div>
  );
}
