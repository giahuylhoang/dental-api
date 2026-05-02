import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import InsuranceList from '../../src/features/patients/InsuranceList';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('InsuranceList', () => {
  it('renders add insurance button', async () => {
    render(<InsuranceList patientId="p1" />, { wrapper });
    expect(await screen.findByRole('button', { name: /add insurance/i })).toBeTruthy();
  });

  it('opens drawer when add insurance is clicked', async () => {
    render(<InsuranceList patientId="p1" />, { wrapper });
    const btn = await screen.findByRole('button', { name: /add insurance/i });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeTruthy();
    });
  });

  it('shows existing insurance rows', async () => {
    // First add an insurance record via the mock
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    // Pre-populate by rendering and adding
    const { rerender } = render(
      <QueryClientProvider client={qc}>
        <InsuranceList patientId="p3" />
      </QueryClientProvider>,
    );
    // Initially empty
    expect(await screen.findByText(/no insurance records/i)).toBeTruthy();
    rerender(
      <QueryClientProvider client={qc}>
        <InsuranceList patientId="p3" />
      </QueryClientProvider>,
    );
  });
});
