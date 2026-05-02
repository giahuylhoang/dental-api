import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import InvoiceList from '../../src/features/billing/InvoiceList';
import { seedInvoices } from '../../src/mocks/pms-f2';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('InvoiceList renders seeded invoices', () => {
  it('renders 12 data rows from MSW fixture', async () => {
    server.use(
      http.get('/api/v2/billing/invoices', () => HttpResponse.json(seedInvoices)),
    );

    render(<InvoiceList />, { wrapper });

    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // 1 header row + 12 data rows
      expect(rows.length).toBe(13);
    });
  });
});
