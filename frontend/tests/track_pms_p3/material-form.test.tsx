import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import MaterialConsumptionForm from '../../src/features/lab/MaterialConsumptionForm';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('MaterialConsumptionForm', () => {
  it('renders form skeleton', () => {
    render(<MaterialConsumptionForm labCaseId="lc1" onSaved={vi.fn()} />, { wrapper });
    expect(screen.getByText(/Qty consumed/i)).toBeInTheDocument();
    expect(screen.getByText(/Unit cost/i)).toBeInTheDocument();
  });

  it('shows placeholder when inventory backend not wired', async () => {
    // inventory endpoints return 404 → error state
    server.use(
      http.get('/api/v2/inventory/items', () =>
        HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
      ),
      http.get('/api/v2/inventory/lots', () =>
        HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
      ),
    );
    render(<MaterialConsumptionForm labCaseId="lc1" onSaved={vi.fn()} />, { wrapper });
    await waitFor(() =>
      expect(screen.getByText(/Inventory backend not wired/i)).toBeInTheDocument(),
    );
  });

  it('renders with inventory list when available', async () => {
    server.use(
      http.get('/api/v2/inventory/items', () =>
        HttpResponse.json([{ id: 'item1', name: 'Acrylic Resin' }]),
      ),
      http.get('/api/v2/inventory/lots', () =>
        HttpResponse.json([{ id: 'lot1', item_id: 'item1', lot_number: 'L001' }]),
      ),
    );
    render(<MaterialConsumptionForm labCaseId="lc1" onSaved={vi.fn()} />, { wrapper });
    await waitFor(() => expect(screen.getByText(/Acrylic Resin/i)).toBeInTheDocument());
    expect(screen.getByText(/L001/i)).toBeInTheDocument();
  });
});
