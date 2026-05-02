import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';

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
  remake_rate: number;
  total_cases: number;
}

function KpiTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function SimpleBar({ rows, labelKey, valueKey, formatValue }: {
  rows: Record<string, unknown>[];
  labelKey: string;
  valueKey: string;
  formatValue: (v: number) => string;
}) {
  const max = Math.max(...rows.map((r) => r[valueKey] as number), 1);
  return (
    <div className="space-y-2">
      {rows.map((r, i) => (
        <div key={i} className="flex items-center gap-2 text-sm">
          <div className="w-32 truncate text-zinc-600">{String(r[labelKey])}</div>
          <div className="flex-1 rounded bg-zinc-100">
            <div
              className="h-4 rounded bg-blue-500"
              style={{ width: `${((r[valueKey] as number) / max) * 100}%` }}
            />
          </div>
          <div className="w-24 text-right text-zinc-700">
            {formatValue(r[valueKey] as number)}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const clinicId = useAuthStore((s) => s.clinicId);

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

  const AR_BUCKETS = kpi?.ar_aging ?? [
    { bucket: '0–30', amount: 0 },
    { bucket: '31–60', amount: 0 },
    { bucket: '61–90', amount: 0 },
    { bucket: '90+', amount: 0 },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Dashboard</h2>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <KpiTile
          label="Production this month"
          value={kpi ? fmt.format(kpi.production_this_month) : '—'}
        />
        <KpiTile
          label="No-show rate"
          value={kpi ? pct(kpi.no_show_rate) : '—'}
        />
        <KpiTile
          label="Lab cost / case"
          value={kpi ? fmt.format(kpi.lab_cost_per_case) : '—'}
        />
        <KpiTile
          label="A/R balance"
          value={kpi ? fmt.format(AR_BUCKETS.reduce((s, b) => s + b.amount, 0)) : '—'}
        />
      </div>

      {/* A/R aging */}
      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold">A/R Aging</h3>
        <div className="grid grid-cols-4 gap-3">
          {AR_BUCKETS.map((b) => (
            <div key={b.bucket} className="rounded bg-zinc-50 p-3 text-center">
              <div className="text-xs text-zinc-500">{b.bucket} days</div>
              <div className="mt-1 font-semibold">{fmt.format(b.amount)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Production by provider */}
      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold">Production by Provider</h3>
        {byProvider.length > 0 ? (
          <SimpleBar
            rows={byProvider as unknown as Record<string, unknown>[]}
            labelKey="provider_name"
            valueKey="production"
            formatValue={fmt.format.bind(fmt)}
          />
        ) : (
          <p className="text-sm text-zinc-400">No data</p>
        )}
      </div>

      {/* Remake rate by lab */}
      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold">Remake Rate by Lab</h3>
        {labRates.length > 0 ? (
          <SimpleBar
            rows={labRates as unknown as Record<string, unknown>[]}
            labelKey="lab_name"
            valueKey="remake_rate"
            formatValue={pct}
          />
        ) : (
          <p className="text-sm text-zinc-400">No data</p>
        )}
      </div>
    </div>
  );
}
