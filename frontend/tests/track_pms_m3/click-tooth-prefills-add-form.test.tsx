import { describe, it, expect } from 'vitest';
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TreatmentPlanEditor from '../../src/features/treatment-plans/TreatmentPlanEditor';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('click tooth pre-fills add form', () => {
  it('clicking tooth #14 sets tooth_number input to 14', async () => {
    render(<TreatmentPlanEditor patientId="p1" planId="tp1" />, { wrapper });

    // E4 redesign: ToothChart lives inside the "Tooth Chart" tab. Click it first.
    await waitFor(() => expect(screen.getByRole('tab', { name: /tooth chart/i })).toBeInTheDocument());
    {
      const t = screen.getByRole('tab', { name: /tooth chart/i });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }

    // Wait for chart to render
    await waitFor(() => {
      const tooth = document.querySelector('[data-tooth="14"]');
      expect(tooth).not.toBeNull();
    });

    const tooth14 = document.querySelector('[data-tooth="14"]')!;
    fireEvent.click(tooth14);

    // Now switch to the Items tab (where the add form lives)
    await waitFor(() => expect(screen.getByRole('tab', { name: /items/i })).toBeInTheDocument());
    {
      const t = screen.getByRole('tab', { name: /items/i });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }

    await waitFor(() => {
      const input = document.querySelector('input[aria-label="tooth_number"]') as HTMLInputElement | null;
      expect(input).not.toBeNull();
      expect(input!.value).toBe('14');
    });
  });
});
