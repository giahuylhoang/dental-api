import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import InvoiceList from '../../src/features/billing/InvoiceList';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('invoice-list-renders-with-ui-input-search', () => {
  it('search input is the D1 <Input> (has data-testid and D1 class)', async () => {
    render(<InvoiceList />, { wrapper });
    const input = await screen.findByTestId('invoice-search');
    expect(input).toBeInTheDocument();
    // D1 Input has 'rounded-md' class
    expect(input.className).toMatch(/rounded-md/);
  });
});
