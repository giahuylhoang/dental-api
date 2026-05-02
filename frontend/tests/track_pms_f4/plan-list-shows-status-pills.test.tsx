import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TreatmentPlansPage from '../../src/features/treatment-plans/TreatmentPlansPage';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('plan list shows status pills', () => {
  it('renders a status pill for each plan with the correct label', async () => {
    render(<TreatmentPlansPage />, { wrapper });

    // Wait for plans to load — seed has 6 plans across all statuses
    await waitFor(() => expect(screen.getAllByText('draft').length).toBeGreaterThan(0));

    // Each status should appear as a pill in the table rows
    expect(screen.getAllByText('draft').length).toBeGreaterThan(0);
    expect(screen.getAllByText('presented').length).toBeGreaterThan(0);
    expect(screen.getAllByText('accepted').length).toBeGreaterThan(0);
    expect(screen.getAllByText('in_progress').length).toBeGreaterThan(0);
    expect(screen.getAllByText('completed').length).toBeGreaterThan(0);
    expect(screen.getAllByText('declined').length).toBeGreaterThan(0);
  });
});
