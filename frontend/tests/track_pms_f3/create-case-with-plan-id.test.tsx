import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import LabCaseCreateForm from '../../src/features/lab/LabCaseCreateForm';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('create-case-with-plan-id', () => {
  it('submits POST /api/v2/lab/cases with treatment_plan_id', async () => {
    const plans = [{ id: 'tp1', status: 'draft', patient_id: 'p1' }];
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.get('/api/v2/treatment-plans', () => HttpResponse.json(plans)),
      http.post('/api/v2/lab/cases', async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 'lc-new', case_number: 'LC-2026-0099' }, { status: 201 });
      }),
    );

    render(<LabCaseCreateForm patientId="p1" />, { wrapper });

    // Wait for plans to load and select one
    await waitFor(() => screen.getByPlaceholderText(/search treatment plans/i));
    fireEvent.change(screen.getByPlaceholderText(/search treatment plans/i), {
      target: { value: 'tp1' },
    });
    await waitFor(() => screen.getByText(/tp1 — draft/i));
    fireEvent.click(screen.getByText(/tp1 — draft/i));

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /create case/i }));

    await waitFor(() => {
      expect(capturedBody).not.toBeNull();
      expect(capturedBody!.treatment_plan_id).toBe('tp1');
    });
  });
});
