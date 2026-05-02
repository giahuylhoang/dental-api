import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { type ColumnDef } from '@tanstack/react-table';
import { DollarSign, UserX, FlaskConical, CreditCard, Calendar, FileText, Users } from 'lucide-react';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/ui/page-header';
import { DataTable } from '@/components/ui/data-table';

const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });
const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

interface KpiData {
  production_this_month: number;
  ar_aging: { bucket: string; amount: number }[];
  no_show_rate: number;
  lab_cost_per_case: number;
}

interface ProviderRow {
  provider_name: string;
  production: number;
}

interface LabRow {
  lab_name: string;
  total_cases: number;
  remake_rate: number;
}

interface ActivityRow {
  time: string;
  type: 'appointment' | 'invoice' | 'lead';
  description: string;
  status: string;
}

const providerColumns: ColumnDef<ProviderRow>[] = [
  { accessorKey: 'provider_name', header: 'Provider' },
  {
    accessorKey: 'production',
    header: 'Production',
    cell: ({ getValue }) => {
      const v = getValue<number>();
      return v ? fmt.format(v) : <span className="text-muted-foreground">—</span>;
    },
  },
];

const labColumns: ColumnDef<LabRow>[] = [
  { accessorKey: 'lab_name', header: 'Lab' },
  { accessorKey: 'total_cases', header: 'Cases' },
  {
    accessorKey: 'remake_rate',
    header: 'Remake Rate',
    cell: ({ getValue }) => pct(getValue<number>()),
  },
];

const activityColumns: ColumnDef<ActivityRow>[] = [
  { accessorKey: 'time', header: 'Time' },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ getValue }) => {
      const t = getValue<string>();
      const Icon = t === 'appointment' ? Calendar : t === 'invoice' ? FileText : Users;
      return <Icon className="h-4 w-4 text-muted-foreground" />;
    },
  },
  { accessorKey: 'description', header: 'Description' },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ getValue }) => <Badge variant="secondary">{getValue<string>()}</Badge>,
  },
];

export default function Dashboard() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const lastUpdated = new Date().toLocaleTimeString();

  const { data: kpi } = useQuery<KpiData>({
    queryKey: ['reporting', 'kpi', clinicId],
    queryFn: () => fetcher<KpiData>('/api/v2/reporting/kpi'),
  });

  const { data: byProvider = [] } = useQuery<ProviderRow[]>({
    queryKey: ['reporting', 'by-provider', clinicId],
    queryFn: () => fetcher<ProviderRow[]>('/api/v2/reporting/production-by-provider'),
  });

  const { data: labRates = [] } = useQuery<LabRow[]>({
    queryKey: ['reporting', 'lab-remake', clinicId],
    queryFn: () => fetcher<LabRow[]>('/api/v2/reporting/remake-rate-by-lab'),
  });

  const { data: appointments = [] } = useQuery<{ id: string; start_time: string; patient_name?: string; status: string }[]>({
    queryKey: ['appointments', 'today', clinicId],
    queryFn: () => fetcher('/api/appointments?today=true'),
  });

  const { data: invoices = [] } = useQuery<{ id: string; created_at: string; patient_name?: string; status: string }[]>({
    queryKey: ['invoices', 'recent', clinicId],
    queryFn: () => fetcher('/api/v2/billing/invoices?days=7'),
  });

  const { data: leads = [] } = useQuery<{ id: string; created_at: string; name?: string; status: string }[]>({
    queryKey: ['leads', 'recent', clinicId],
    queryFn: () => fetcher('/api/leads?days=7'),
  });

  const AR_BUCKETS = kpi?.ar_aging ?? [
    { bucket: '0–30', amount: 0 },
    { bucket: '31–60', amount: 0 },
    { bucket: '61–90', amount: 0 },
    { bucket: '90+', amount: 0 },
  ];

  const activityRows: ActivityRow[] = [
    ...appointments.map((a) => ({
      time: new Date(a.start_time).toLocaleTimeString(),
      type: 'appointment' as const,
      description: a.patient_name ?? 'Appointment',
      status: a.status,
    })),
    ...invoices.map((i) => ({
      time: new Date(i.created_at).toLocaleTimeString(),
      type: 'invoice' as const,
      description: i.patient_name ?? 'Invoice',
      status: i.status,
    })),
    ...leads.map((l) => ({
      time: new Date(l.created_at).toLocaleTimeString(),
      type: 'lead' as const,
      description: l.name ?? 'Lead',
      status: l.status,
    })),
  ]
    .sort((a, b) => b.time.localeCompare(a.time))
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description={`Last updated ${lastUpdated}`}
        actions={
          <>
            <Button variant="outline">Date range</Button>
            <Button onClick={() => {}}>Export</Button>
          </>
        }
      />

      {/* KPI tiles */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card data-testid="kpi-tile">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm text-muted-foreground">Production this month</span>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {kpi ? fmt.format(kpi.production_this_month) : <span className="text-muted-foreground">—</span>}
            </div>
          </CardContent>
          <CardFooter>
            <Badge variant="success">+12%</Badge>
          </CardFooter>
        </Card>

        <Card data-testid="kpi-tile">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm text-muted-foreground">No-show rate</span>
            <UserX className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {kpi ? pct(kpi.no_show_rate) : <span className="text-muted-foreground">—</span>}
            </div>
          </CardContent>
          <CardFooter>
            <Badge variant="destructive">+0.4%</Badge>
          </CardFooter>
        </Card>

        <Card data-testid="kpi-tile">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm text-muted-foreground">Lab cost / case</span>
            <FlaskConical className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {kpi ? fmt.format(kpi.lab_cost_per_case) : <span className="text-muted-foreground">—</span>}
            </div>
          </CardContent>
          <CardFooter>
            <Badge variant="secondary">—</Badge>
          </CardFooter>
        </Card>

        <Card data-testid="kpi-tile">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm text-muted-foreground">A/R balance</span>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {kpi
                ? fmt.format(AR_BUCKETS.reduce((s, b) => s + b.amount, 0))
                : <span className="text-muted-foreground">—</span>}
            </div>
          </CardContent>
          <CardFooter>
            <Badge variant="secondary">—</Badge>
          </CardFooter>
        </Card>
      </div>

      {/* A/R Aging */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>A/R Aging</CardTitle>
          <Button variant="link" asChild>
            <Link to="/billing?status=overdue">View overdue invoices</Link>
          </Button>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            {AR_BUCKETS.map((b) => (
              <div key={b.bucket} className="flex-1 rounded-lg border p-3 text-center">
                <div className="text-xs text-muted-foreground">{b.bucket} days</div>
                <div className="mt-1 font-semibold">
                  {b.amount ? fmt.format(b.amount) : <span className="text-muted-foreground">—</span>}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Production by Provider + Remake Rate by Lab */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Production by Provider</CardTitle>
          </CardHeader>
          <CardContent>
            {byProvider.length > 0 ? (
              <DataTable data-testid="provider-table" columns={providerColumns} data={byProvider} />
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 text-center">
                <DollarSign className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No data yet</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Remake Rate by Lab</CardTitle>
          </CardHeader>
          <CardContent>
            {labRates.length > 0 ? (
              <DataTable data-testid="lab-table" columns={labColumns} data={labRates} />
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 text-center">
                <FlaskConical className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No data yet</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          {activityRows.length > 0 ? (
            <DataTable columns={activityColumns} data={activityRows} />
          ) : (
            <div className="flex flex-col items-center gap-2 py-8 text-center">
              <Calendar className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No data yet</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
