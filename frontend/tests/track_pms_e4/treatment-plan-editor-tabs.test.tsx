import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import TreatmentPlanEditor from '../../src/features/treatment-plans/TreatmentPlanEditor';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

const plan = {
  id: 'tp-tabs-1',
  patient_id: 'p1',
  status: 'draft',
  total_estimate: 1500,
  insurance_estimate: 750,
  patient_estimate: 750,
  items: [],
};

describe('treatment-plan-editor-tabs', () => {
  it('renders 4 D1 Tabs: Items, Tooth Chart, Care Notes, History', async () => {
    server.use(
      http.get('/api/v2/treatment-plans/tp-tabs-1', () => HttpResponse.json(plan)),
    );

    render(<TreatmentPlanEditor patientId="p1" planId="tp-tabs-1" />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /items/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /tooth chart/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /care notes/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /history/i })).toBeInTheDocument();
    });
  });
});
