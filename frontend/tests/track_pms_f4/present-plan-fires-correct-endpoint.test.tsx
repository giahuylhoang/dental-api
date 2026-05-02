import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

describe('present plan fires correct endpoint', () => {
  it('POSTs to /api/v2/treatment-plans/{id}/present when Present is clicked', async () => {
    let capturedUrl: string | null = null;

    server.use(
      http.post('/api/v2/treatment-plans/tp1/present', ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json({ id: 'tp1', status: 'presented', patient_id: 'p1', total_estimate: 1500, insurance_estimate: 750, patient_estimate: 750, items: [] });
      }),
    );

    render(<TreatmentPlanEditor patientId="p1" planId="tp1" />, { wrapper });

    // Wait for plan to load (tp1 is draft)
    await waitFor(() => expect(screen.getByRole('button', { name: /present/i })).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /present/i }));

    await waitFor(() => expect(capturedUrl).not.toBeNull());
    expect(capturedUrl).toMatch(/\/api\/v2\/treatment-plans\/tp1\/present$/);
  });
});
