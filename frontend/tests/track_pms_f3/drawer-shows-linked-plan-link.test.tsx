import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import LabCaseDrawer from '../../src/features/lab/LabCaseDrawer';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

const caseWithPlan = {
  id: 'lc1',
  case_number: 'LC-2026-0001',
  denture_case_id: 'dc1',
  vendor_id: 'v1',
  status: 'sent',
  sent_at: null,
  due_back_at: null,
  returned_at: null,
  remake_of_id: null,
  remake_reason: null,
  lab_fee: 350,
  courier_tracking: null,
  treatment_plan_id: 'tp1',
};

const caseNoPlan = { ...caseWithPlan, id: 'lc2', treatment_plan_id: null };

describe('drawer-shows-linked-plan-link', () => {
  it('shows Open plan link when treatment_plan_id is set', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json([caseWithPlan])),
      http.get('/api/v2/treatment-plans/tp1', () =>
        HttpResponse.json({ id: 'tp1', status: 'draft', patient_id: 'p1' }),
      ),
    );

    render(
      <LabCaseDrawer caseId="lc1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /open plan/i });
      expect(link).toBeInTheDocument();
      expect(link.getAttribute('href')).toContain('/plans');
    });
  });

  it('hides Linked Treatment Plan section when treatment_plan_id is null', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json([caseNoPlan])),
    );

    render(
      <LabCaseDrawer caseId="lc2" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => screen.getAllByText(/Precision Dental Lab/i)[0]);
    expect(screen.queryByText(/Linked Treatment Plan/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /open plan/i })).not.toBeInTheDocument();
  });
});
