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

describe('treatment-plan-editor-status-buttons', () => {
  it('shows "Present" button for a draft plan', async () => {
    server.use(
      http.get('/api/v2/treatment-plans/tp-draft', () =>
        HttpResponse.json({
          id: 'tp-draft',
          patient_id: 'p1',
          status: 'draft',
          total_estimate: 1000,
          insurance_estimate: 500,
          patient_estimate: 500,
          items: [],
        }),
      ),
    );

    render(<TreatmentPlanEditor patientId="p1" planId="tp-draft" />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /present/i })).toBeInTheDocument();
    });
  });

  it('shows "Mark in progress" button for an accepted plan', async () => {
    server.use(
      http.get('/api/v2/treatment-plans/tp-accepted', () =>
        HttpResponse.json({
          id: 'tp-accepted',
          patient_id: 'p1',
          status: 'accepted',
          total_estimate: 1000,
          insurance_estimate: 500,
          patient_estimate: 500,
          items: [],
        }),
      ),
    );

    render(<TreatmentPlanEditor patientId="p1" planId="tp-accepted" />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /mark in progress/i })).toBeInTheDocument();
    });
  });
});
