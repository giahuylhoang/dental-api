import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LabCaseDrawer from '../../src/features/lab/LabCaseDrawer';

const labCase = {
  id: 'lc-sheet-1',
  case_number: 'LC-SHEET-001',
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
  treatment_plan_id: null,
  patient_id: 'p1',
};

const patient = {
  id: 'p1',
  first_name: 'Bob',
  last_name: 'Jones',
  phone: '555-0002',
  email: 'bob@example.com',
  date_of_birth: '1975-06-15',
  status: 'active',
  clinic_id: 'default',
};

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('lab-drawer-uses-sheet', () => {
  it('renders a Radix Sheet (data-[state] attribute present on content)', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json([labCase])),
      http.get('/api/v2/lab/vendors', () => HttpResponse.json([{ id: 'v1', name: 'Test Lab' }])),
      http.get('/api/patients/:id', () => HttpResponse.json(patient)),
    );

    render(
      <LabCaseDrawer caseId="lc-sheet-1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => {
      // Radix Sheet content is portalled to document.body, use document.querySelector
      const sheetContent = document.querySelector('[role="dialog"][data-state="open"]');
      expect(sheetContent).not.toBeNull();
    });
  });

  it('shows D1 Tabs in the drawer', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json([labCase])),
      http.get('/api/v2/lab/vendors', () => HttpResponse.json([{ id: 'v1', name: 'Test Lab' }])),
      http.get('/api/patients/:id', () => HttpResponse.json(patient)),
    );

    render(
      <LabCaseDrawer caseId="lc-sheet-1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /detail/i })).toBeInTheDocument();
    });
  });
});
