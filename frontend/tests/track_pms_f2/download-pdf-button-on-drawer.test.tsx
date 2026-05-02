import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import InvoiceDrawer from '../../src/features/billing/InvoiceDrawer';

const fixture = {
  id: 'inv-dl-1',
  invoice_number: 'INV-DL-001',
  patient_id: 'p1',
  patient_name: 'Download Patient',
  status: 'issued' as const,
  subtotal: 100,
  gst: 5,
  total: 105,
  total_cents: 10500,
  balance: 105,
  lines: [{ id: 'l1', description: 'Cleaning', qty: 1, unit_price_cents: 10000 }],
  created_at: '2024-01-01T00:00:00Z',
};

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Download PDF button on InvoiceDrawer', () => {
  it('renders a Download PDF button and calls URL.createObjectURL on click', async () => {
    const createObjectURL = vi.fn().mockReturnValue('blob:http://localhost/fake');
    const revokeObjectURL = vi.fn();
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL });

    // Stub anchor click to avoid navigation
    const origCreate = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag === 'a') {
        const a = origCreate('a');
        a.click = vi.fn();
        return a;
      }
      return origCreate(tag);
    });

    render(<InvoiceDrawer invoice={fixture} onClose={vi.fn()} />, { wrapper });

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /download.*pdf/i })).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole('button', { name: /download.*pdf/i }));

    await waitFor(() => expect(createObjectURL).toHaveBeenCalled(), { timeout: 10000 });

    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  }, 15000);
});
