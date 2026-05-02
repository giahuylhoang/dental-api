import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
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

describe('Dashboard uses Card and DataTable (E2)', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v2/reporting/kpi', () =>
        HttpResponse.json({
          production_this_month: 10000,
          ar_aging: [
            { bucket: '0–30', amount: 100 },
            { bucket: '31–60', amount: 200 },
            { bucket: '61–90', amount: 300 },
            { bucket: '90+', amount: 400 },
          ],
          no_show_rate: 0.05,
          lab_cost_per_case: 200,
        }),
      ),
      http.get('/api/v2/reporting/production-by-provider', () =>
        HttpResponse.json([
          { provider_name: 'Dr. A', production: 5000 },
          { provider_name: 'Dr. B', production: 5000 },
        ]),
      ),
      http.get('/api/v2/reporting/remake-rate-by-lab', () =>
        HttpResponse.json([{ lab_name: 'Lab X', total_cases: 5, remake_rate: 0.1 }]),
      ),
      http.get('/api/appointments', () => HttpResponse.json([])),
      http.get('/api/v2/billing/invoices', () => HttpResponse.json([])),
      http.get('/api/leads', () => HttpResponse.json([])),
    );
  });

  it('renders ≥6 Card root elements', () => {
    render(<Dashboard />, { wrapper });
    // Card root class from shadcn: rounded-lg border bg-card
    const cards = document.querySelectorAll('.rounded-lg.border.bg-card');
    expect(cards.length).toBeGreaterThanOrEqual(6);
  });

  it('renders ≥2 DataTable elements (rounded-md border)', async () => {
    const { findAllByRole } = render(<Dashboard />, { wrapper });
    // DataTable renders a table element; wait for data
    const tables = await findAllByRole('table');
    expect(tables.length).toBeGreaterThanOrEqual(2);
  });
});
