import { describe, it, expect } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/react';
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

    // Wait for chart to render
    await waitFor(() => {
      const tooth = document.querySelector('[data-tooth="14"]');
      expect(tooth).not.toBeNull();
    });

    const tooth14 = document.querySelector('[data-tooth="14"]')!;
    fireEvent.click(tooth14);

    await waitFor(() => {
      const input = document.querySelector('input[aria-label="tooth_number"]') as HTMLInputElement | null;
      expect(input).not.toBeNull();
      expect(input!.value).toBe('14');
    });
  });
});
