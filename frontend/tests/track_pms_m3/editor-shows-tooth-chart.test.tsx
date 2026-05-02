import { describe, it, expect } from 'vitest';
import { render, waitFor } from '@testing-library/react';
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

describe('TreatmentPlanEditor shows tooth chart', () => {
  it('renders an SVG element for the tooth chart', async () => {
    render(<TreatmentPlanEditor patientId="p1" planId="tp1" />, { wrapper });
    await waitFor(() => {
      const svg = document.querySelector('svg');
      expect(svg).not.toBeNull();
    });
  });
});
