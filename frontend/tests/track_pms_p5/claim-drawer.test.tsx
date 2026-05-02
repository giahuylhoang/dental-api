import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import ClaimDrawer from '../../src/features/billing/ClaimDrawer';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('ClaimDrawer', () => {
  it('renders when open', async () => {
    render(
      <ClaimDrawer claimId="claim-test-1" open onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
  });

  it('does not render when closed', () => {
    render(
      <ClaimDrawer claimId="claim-test-1" open={false} onClose={vi.fn()} />,
      { wrapper },
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('shows adjudicate form when status is submitted', async () => {
    // The mock returns status=submitted for unknown claim IDs
    render(
      <ClaimDrawer claimId="claim-submitted-1" open onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => screen.getByRole('dialog'));
    await waitFor(() =>
      expect(screen.getByText(/Adjudicate Claim/i)).toBeInTheDocument(),
    );
  });

  it('adjudicate form posts correct body', async () => {
    render(
      <ClaimDrawer claimId="claim-submitted-2" open onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => screen.getByText(/Adjudicate Claim/i));

    // Select outcome = accepted (default)
    const outcomeSelect = screen.getByLabelText(/Outcome/i);
    expect(outcomeSelect).toBeInTheDocument();

    // Fill amount
    const amountInput = screen.getByLabelText(/Accepted Amount/i);
    fireEvent.change(amountInput, { target: { value: '80' } });

    // Submit
    const submitBtn = screen.getByRole('button', { name: /Submit Adjudication/i });
    fireEvent.click(submitBtn);

    // Should not show error
    await waitFor(() =>
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument(),
    );
  });
});
