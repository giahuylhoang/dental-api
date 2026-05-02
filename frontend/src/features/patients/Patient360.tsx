import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import { Card, CardContent } from '../../components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import { Button } from '../../components/ui/button';
import { PatientChip } from './PatientChip';
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
  'Appointments',
  'Documents',
  'Insurance',
  'Treatment Plans',
  'Lab Cases',
  'Communications',
  'Notes',
] as const;

type Tab = (typeof TABS)[number];

const TAB_PARAM: Record<Tab, string> = {
  Overview: 'overview',
  Appointments: 'appointments',
  Documents: 'documents',
  Insurance: 'insurance',
  'Treatment Plans': 'treatment-plans',
  'Lab Cases': 'lab-cases',
  Communications: 'communications',
  Notes: 'notes',
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
        <div><span className="text-zinc-500">DOB:</span> {patient.date_of_birth ?? '—'}</div>
        <div><span className="text-zinc-500">Age:</span> {computeAge(patient.date_of_birth)}</div>
        <div><span className="text-zinc-500">Phone:</span> {patient.phone ?? '—'}</div>
        <div><span className="text-zinc-500">Email:</span> {patient.email ?? '—'}</div>
        <div><span className="text-zinc-500">Status:</span> {patient.status}</div>
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
        <div key={tp.id} className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2">
          <span>Plan #{tp.id}</span>
          <span className="text-zinc-500">{tp.status}</span>
          <span>${tp.total_estimate.toFixed(2)}</span>
        </div>
      ))}
      {data?.length === 0 && <p className="text-zinc-500">No treatment plans.</p>}
    </div>
  );
}

function LabCasesTab({ patientId }: { patientId: string }) {
  const { data } = useQuery({
    queryKey: ['denture-cases', patientId],
    queryFn: () =>
      fetcher<Array<{ id: string; arch: string; case_type: string; current_stage: string; status: string }>>(
        `/api/v2/clinical/patients/${patientId}/denture-cases`,
      ),
  });
  return (
    <div className="space-y-2 text-sm">
      {data?.map((dc) => (
        <div key={dc.id} className="flex items-center gap-3 rounded border border-zinc-200 px-3 py-2">
          <span className="font-medium">{dc.arch} / {dc.case_type}</span>
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">{dc.current_stage}</span>
          <span className={`rounded-full px-2 py-0.5 text-xs ${dc.status === 'open' ? 'bg-green-100 text-green-700' : 'bg-zinc-100 text-zinc-600'}`}>
            {dc.status}
          </span>
        </div>
      ))}
      {data?.length === 0 && <p className="text-zinc-500">No lab cases.</p>}
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
        <div key={a.id} className="flex items-center gap-3 rounded border border-zinc-200 px-3 py-2">
          <span>{a.start_time}</span>
          <span className="text-zinc-500">{a.status}</span>
        </div>
      ))}
      {data?.length === 0 && <p className="text-zinc-500">No appointments.</p>}
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
      {/* Sticky header */}
      <div className="sticky top-0 z-10 bg-background border-b pb-3 mb-4">
        <div className="flex items-center justify-between gap-4 pt-3">
          <PatientChip patientId={patient.id} variant="card" />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">Actions ▾</Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>New appointment</DropdownMenuItem>
              <DropdownMenuItem>Send message</DropdownMenuItem>
              <DropdownMenuItem>Print summary</DropdownMenuItem>
              <DropdownMenuItem>Archive</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <Tabs value={TAB_PARAM[activeTab]} onValueChange={(v) => setTab(PARAM_TO_TAB[v] ?? 'Overview')}>
        <TabsList className="mb-4 flex-wrap h-auto gap-1">
          {TABS.map((tab) => (
            <TabsTrigger key={tab} value={TAB_PARAM[tab]}>
              {tab}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview">
          <Card><CardContent className="pt-4"><OverviewTab patient={patient} /></CardContent></Card>
        </TabsContent>
        <TabsContent value="appointments">
          <Card><CardContent className="pt-4"><AppointmentsTab patientId={patient.id} /></CardContent></Card>
        </TabsContent>
        <TabsContent value="documents">
          <Card>
            <CardContent className="pt-4 space-y-6">
              <DocumentUploader patientId={patient.id} defaultKind="other" />
              <DocumentList patientId={patient.id} />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="insurance">
          <Card><CardContent className="pt-4"><InsuranceList patientId={patient.id} /></CardContent></Card>
        </TabsContent>
        <TabsContent value="treatment-plans">
          <Card><CardContent className="pt-4"><TreatmentPlansTab patientId={patient.id} /></CardContent></Card>
        </TabsContent>
        <TabsContent value="lab-cases">
          <Card><CardContent className="pt-4"><LabCasesTab patientId={patient.id} /></CardContent></Card>
        </TabsContent>
        <TabsContent value="communications">
          <Card><CardContent className="pt-4"><CommunicationsTab patientId={patient.id} /></CardContent></Card>
        </TabsContent>
        <TabsContent value="notes">
          <Card><CardContent className="pt-4"><NotesPanel patientId={patient.id} /></CardContent></Card>
        </TabsContent>
      </Tabs>

      {/* Legacy tabs still accessible via direct URL params */}
      {searchParams.get('tab') === 'status' && <LifecyclePanel patientId={patient.id} />}
      {searchParams.get('tab') === 'medical' && <MedicalForm patientId={patient.id} />}
      {searchParams.get('tab') === 'tooth-chart' && <ToothChart patientId={patient.id} />}
    </div>
  );
}
