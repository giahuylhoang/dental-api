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

describe('Dashboard empty state (E2)', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v2/reporting/kpi', () =>
        HttpResponse.json({
          production_this_month: 0,
          ar_aging: [
            { bucket: '0–30', amount: 0 },
            { bucket: '31–60', amount: 0 },
            { bucket: '61–90', amount: 0 },
            { bucket: '90+', amount: 0 },
          ],
          no_show_rate: 0,
          lab_cost_per_case: 0,
        }),
      ),
      http.get('/api/v2/reporting/production-by-provider', () => HttpResponse.json([])),
      http.get('/api/v2/reporting/remake-rate-by-lab', () => HttpResponse.json([])),
      http.get('/api/appointments', () => HttpResponse.json([])),
      http.get('/api/v2/billing/invoices', () => HttpResponse.json([])),
      http.get('/api/leads', () => HttpResponse.json([])),
    );
  });

  it('renders without crashing when all data is empty', () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders 4 KPI tiles even with zero values', () => {
    render(<Dashboard />, { wrapper });
    const tiles = document.querySelectorAll('[data-testid="kpi-tile"]');
    expect(tiles.length).toBe(4);
  });

  it('renders A/R Aging with 4 buckets showing empty state', () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText('A/R Aging')).toBeInTheDocument();
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });

  it('renders empty state for Production by Provider', () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText('Production by Provider')).toBeInTheDocument();
    const noDataMessages = screen.getAllByText('No data yet');
    expect(noDataMessages.length).toBeGreaterThanOrEqual(1);
  });

  it('renders empty state for Recent activity', () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText('Recent activity')).toBeInTheDocument();
  });
});
