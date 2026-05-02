import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import InvoiceList from '../../src/features/billing/InvoiceList';

const INVOICES = [
  {
    id: 'inv-1',
    invoice_number: 'INV-001',
    patient_id: 'p1',
    patient_name: 'Alice Johnson',
    status: 'issued',
    subtotal: 100,
    gst: 5,
    total: 105,
    total_cents: 10500,
    balance: 105,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'inv-2',
    invoice_number: 'INV-002',
    patient_id: 'p2',
    patient_name: 'Bob Smith',
    status: 'paid',
    subtotal: 200,
    gst: 10,
    total: 210,
    total_cents: 21000,
    balance: 0,
    created_at: '2024-01-02T00:00:00Z',
  },
];

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('InvoiceList fuzzy search', () => {
  it('filters to rows matching "ali" (case-insensitive)', async () => {
    server.use(
      http.get('/api/v2/billing/invoices', () => HttpResponse.json(INVOICES)),
      http.get('/api/v2/clinical/patients/:id/denture-cases', () => HttpResponse.json([])),
    );

    render(<InvoiceList />, { wrapper });

    // Wait for invoices to load
    await waitFor(() => expect(screen.getByText('Alice Johnson')).toBeInTheDocument());
    expect(screen.getByText('Bob Smith')).toBeInTheDocument();

    const input = screen.getByRole('searchbox');
    fireEvent.change(input, { target: { value: 'ali' } });

    // Wait for debounce (200ms) + re-render
    await waitFor(
      () => expect(screen.queryByText('Bob Smith')).not.toBeInTheDocument(),
      { timeout: 1000 },
    );
    expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
  }, 10000);
});
