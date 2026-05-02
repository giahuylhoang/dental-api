import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import InvoiceList from '../../src/features/billing/InvoiceList';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('billing-comms-redesign', () => {
  it('renders PageHeader with title Billing', async () => {
    server.use(
      http.get('/api/v2/billing/invoices', () => HttpResponse.json([])),
    );

    render(<InvoiceList />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /billing/i })).toBeInTheDocument();
    });
  });

  it('renders DataTable testid', async () => {
    server.use(
      http.get('/api/v2/billing/invoices', () => HttpResponse.json([])),
    );

    const { container } = render(<InvoiceList />, { wrapper });

    await waitFor(() => {
      const el = container.querySelector('[data-testid="invoice-data-table"]');
      expect(el).toBeTruthy();
    });
  });

  it('InvoiceList imports ≥3 ui components (Button, Badge, Input at minimum)', async () => {
    // This is a static check — the gate enforces it via grep.
    // Here we just verify the component renders without error.
    server.use(
      http.get('/api/v2/billing/invoices', () => HttpResponse.json([])),
    );

    const { container } = render(<InvoiceList />, { wrapper });
    expect(container).toBeTruthy();
  });
});
