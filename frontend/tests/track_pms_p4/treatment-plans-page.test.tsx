import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

describe('TreatmentPlansPage', () => {
  it('renders the plans list', async () => {
    render(<TreatmentPlansPage />, { wrapper });
    await waitFor(() => expect(screen.getByText('Treatment Plans')).toBeInTheDocument());
    // The mock has one plan with patient_id p1 → patient_name "Alice Smith"
    await waitFor(() => expect(screen.getByText(/Alice Smith/i)).toBeInTheDocument());
  });

  it('filter chips render all statuses', async () => {
    render(<TreatmentPlansPage />, { wrapper });
    await waitFor(() => screen.getByText('Treatment Plans'));
    expect(screen.getByRole('button', { name: /draft/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /accepted/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /completed/i })).toBeInTheDocument();
  });

  it('filter chip hides non-matching plans', async () => {
    render(<TreatmentPlansPage />, { wrapper });
    await waitFor(() => screen.getByText(/Alice Smith/i));

    // Click "accepted" filter — the mock plan is "draft", so it should disappear
    fireEvent.click(screen.getByRole('button', { name: /^accepted$/i }));
    await waitFor(() => expect(screen.queryByText(/Alice Smith/i)).not.toBeInTheDocument());
  });

  it('search filters by patient name', async () => {
    render(<TreatmentPlansPage />, { wrapper });
    await waitFor(() => screen.getByText(/Alice Smith/i));

    const searchInput = screen.getByPlaceholderText(/search by patient name/i);
    fireEvent.change(searchInput, { target: { value: 'Bob' } });
    await waitFor(() => expect(screen.queryByText(/Alice Smith/i)).not.toBeInTheDocument());
  });
});
