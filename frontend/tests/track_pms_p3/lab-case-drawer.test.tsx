import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import LabCaseDrawer from '../../src/features/lab/LabCaseDrawer';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('LabCaseDrawer', () => {
  it('renders with mocked GET response', async () => {
    render(
      <LabCaseDrawer caseId="lc1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => expect(screen.getByText(/Precision Dental Lab/i)).toBeInTheDocument());
    expect(screen.getByText(/sent/i)).toBeInTheDocument();
  });

  it('tabs switch correctly', async () => {
    render(
      <LabCaseDrawer caseId="lc1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => screen.getByText(/Precision Dental Lab/i));

    // Switch to Implants tab
    fireEvent.click(screen.getByRole('button', { name: /implants/i }));
    await waitFor(() => expect(screen.getByText(/Lot number/i)).toBeInTheDocument());

    // Switch to Materials tab
    fireEvent.click(screen.getByRole('button', { name: /materials/i }));
    await waitFor(() => expect(screen.getByText(/Qty consumed/i)).toBeInTheDocument());
  });

  it('does not render when closed', () => {
    render(
      <LabCaseDrawer caseId="lc1" open={false} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    expect(screen.queryByText(/Lab Case/i)).not.toBeInTheDocument();
  });
});
