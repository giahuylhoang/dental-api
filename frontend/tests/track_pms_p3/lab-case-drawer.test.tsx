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
    await waitFor(() => expect(screen.getAllByText(/Precision Dental Lab/i).length).toBeGreaterThan(0));
    // E4 redesign: status appears in multiple places (header badge + body) — use getAllByText
    expect(screen.getAllByText(/sent/i).length).toBeGreaterThan(0);
  });

  it('tabs switch correctly', async () => {
    render(
      <LabCaseDrawer caseId="lc1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => screen.getAllByText(/Precision Dental Lab/i)[0]);

    // E4 redesign: Drawer uses Radix Tabs (role=tab) and needs pointerDown sequence
    {
      const t = screen.getByRole('tab', { name: /implants/i });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }
    await waitFor(() => expect(screen.getByText(/Lot number/i)).toBeInTheDocument());

    {
      const t = screen.getByRole('tab', { name: /materials/i });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }
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
