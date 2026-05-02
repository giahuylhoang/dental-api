import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import Dashboard from '../../src/features/reporting/Dashboard';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

const kpiData = {
  production_this_month: 42000,
  ar_aging: [
    { bucket: '0–30', amount: 5000 },
    { bucket: '31–60', amount: 2000 },
    { bucket: '61–90', amount: 1000 },
    { bucket: '90+', amount: 500 },
  ],
  no_show_rate: 0.08,
  lab_cost_per_case: 350,
};

const providerData = [
  { provider_name: 'Dr. Smith', production: 20000 },
  { provider_name: 'Dr. Jones', production: 22000 },
];

const labData = [
  { lab_name: 'Acme Lab', total_cases: 10, remake_rate: 0.05 },
];

describe('Dashboard redesign (E2)', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v2/reporting/kpi', () => HttpResponse.json(kpiData)),
      http.get('/api/v2/reporting/production-by-provider', () => HttpResponse.json(providerData)),
      http.get('/api/v2/reporting/remake-rate-by-lab', () => HttpResponse.json(labData)),
      http.get('/api/appointments', () => HttpResponse.json([])),
      http.get('/api/v2/billing/invoices', () => HttpResponse.json([])),
      http.get('/api/leads', () => HttpResponse.json([])),
    );
  });

  it('renders PageHeader with title "Dashboard"', () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders 4 KPI tiles', () => {
    render(<Dashboard />, { wrapper });
    const tiles = document.querySelectorAll('[data-testid="kpi-tile"]');
    expect(tiles.length).toBe(4);
  });

  it('renders A/R Aging card with 4 buckets', () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText('A/R Aging')).toBeInTheDocument();
    expect(screen.getByText('0–30 days')).toBeInTheDocument();
    expect(screen.getByText('31–60 days')).toBeInTheDocument();
    expect(screen.getByText('61–90 days')).toBeInTheDocument();
    expect(screen.getByText('90+ days')).toBeInTheDocument();
  });

  it('renders Production by Provider and Remake Rate by Lab DataTables', async () => {
    render(<Dashboard />, { wrapper });
    // Wait for data to load
    expect(await screen.findByText('Dr. Smith')).toBeInTheDocument();
    expect(await screen.findByText('Acme Lab')).toBeInTheDocument();
  });

  it('renders Recent activity section', () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText('Recent activity')).toBeInTheDocument();
  });
});
