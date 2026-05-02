import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import InvoiceList from '../../src/features/billing/InvoiceList';

const INVOICES = [
  {
    id: 'inv-a', invoice_number: 'INV-A', patient_id: 'p1', patient_name: 'Alice',
    status: 'issued', subtotal: 100, gst: 0, total: 100, total_cents: 10000, balance: 100,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'inv-b', invoice_number: 'INV-B', patient_id: 'p2', patient_name: 'Bob',
    status: 'paid', subtotal: 500, gst: 0, total: 500, total_cents: 50000, balance: 0,
    created_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 'inv-c', invoice_number: 'INV-C', patient_id: 'p3', patient_name: 'Carol',
    status: 'draft', subtotal: 250, gst: 0, total: 250, total_cents: 25000, balance: 250,
    created_at: '2024-01-03T00:00:00Z',
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

describe('Sort by Total', () => {
  it('sorts descending then ascending on Total header click', async () => {
    server.use(
      http.get('/api/v2/billing/invoices', () => HttpResponse.json(INVOICES)),
    );

    render(<InvoiceList />, { wrapper });

    await waitFor(() => expect(screen.getByText('Alice')).toBeInTheDocument());

    const totalHeader = screen.getByRole('columnheader', { name: /total/i });

    // First click → descending (500, 250, 100)
    fireEvent.click(totalHeader);
    await waitFor(() => {
      const rows = screen.getAllByRole('row').slice(1); // skip header
      expect(rows[0]).toHaveTextContent('Bob');
      expect(rows[1]).toHaveTextContent('Carol');
      expect(rows[2]).toHaveTextContent('Alice');
    });

    // Second click → ascending (100, 250, 500)
    fireEvent.click(totalHeader);
    await waitFor(() => {
      const rows = screen.getAllByRole('row').slice(1);
      expect(rows[0]).toHaveTextContent('Alice');
      expect(rows[1]).toHaveTextContent('Carol');
      expect(rows[2]).toHaveTextContent('Bob');
    });
  });
});
