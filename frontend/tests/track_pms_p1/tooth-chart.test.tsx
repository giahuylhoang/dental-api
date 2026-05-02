import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import ToothChart from '../../src/features/patients/ToothChart';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('ToothChart', () => {
  it('renders 32 teeth', async () => {
    render(<ToothChart patientId="p1" />, { wrapper });
    await waitFor(() => {
      const teeth = document.querySelectorAll('[data-tooth]');
      if (teeth.length !== 32) throw new Error(`Expected 32 teeth, got ${teeth.length}`);
    });
    expect(document.querySelectorAll('[data-tooth]').length).toBe(32);
  });

  it('clicking a tooth opens popover', async () => {
    render(<ToothChart patientId="p1" />, { wrapper });
    await waitFor(() => {
      const teeth = document.querySelectorAll('[data-tooth]');
      if (teeth.length !== 32) throw new Error('teeth not loaded');
    });
    const tooth1 = document.querySelector('[data-tooth="1"]');
    expect(tooth1).not.toBeNull();
    fireEvent.click(tooth1!);
    await waitFor(() => {
      expect(screen.getByText(/tooth #1/i)).toBeTruthy();
    });
  });

  it('saves single-tooth update', async () => {
    render(<ToothChart patientId="p1" />, { wrapper });
    await waitFor(() => {
      const teeth = document.querySelectorAll('[data-tooth]');
      if (teeth.length !== 32) throw new Error('teeth not loaded');
    });
    const tooth5 = document.querySelector('[data-tooth="5"]');
    expect(tooth5).not.toBeNull();
    fireEvent.click(tooth5!);
    await waitFor(() => screen.getByText(/tooth #5/i));

    const statusSelect = screen.getByLabelText(/status/i);
    fireEvent.change(statusSelect, { target: { value: 'extracted' } });

    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    await waitFor(() => {
      expect(screen.queryByText(/tooth #5/i)).toBeNull();
    });
  });
});
