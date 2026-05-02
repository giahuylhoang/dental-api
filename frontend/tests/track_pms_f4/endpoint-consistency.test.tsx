import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http } from 'msw';
import { server } from '../../src/mocks/server';
import TreatmentPlansPage from '../../src/features/treatment-plans/TreatmentPlansPage';
import TreatmentPlanEditor from '../../src/features/treatment-plans/TreatmentPlanEditor';

const capturedUrls: string[] = [];

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('endpoint consistency', () => {
  it('no plan-related calls use the old clinical patients path', async () => {
    capturedUrls.length = 0;

    // Intercept all requests and record URLs
    server.use(
      http.all('*', ({ request }) => {
        capturedUrls.push(request.url);
        return undefined; // pass through to existing handlers
      }),
    );

    // Render list page — triggers GET /api/v2/treatment-plans
    render(<TreatmentPlansPage />, { wrapper });
    await waitFor(() => screen.getByText('Treatment Plans'));
    await waitFor(() => capturedUrls.some((u) => u.includes('/api/v2/treatment-plans')));

    // Assert no URL matches the old clinical path
    const badUrls = capturedUrls.filter((u) =>
      /\/api\/v2\/clinical\/patients\/.+\/treatment-plans/.test(u),
    );
    expect(badUrls).toHaveLength(0);

    // Assert all treatment-plan-related calls use the correct base path
    const planUrls = capturedUrls.filter((u) => u.includes('treatment-plan'));
    expect(planUrls.length).toBeGreaterThan(0);
    planUrls.forEach((u) => {
      expect(u).toMatch(/\/api\/v2\/treatment-plans/);
    });
  });

  it('TreatmentPlanEditor load uses /api/v2/treatment-plans/{id}', async () => {
    capturedUrls.length = 0;

    server.use(
      http.all('*', ({ request }) => {
        capturedUrls.push(request.url);
        return undefined;
      }),
    );

    render(<TreatmentPlanEditor patientId="p1" planId="tp1" />, { wrapper });
    await waitFor(() => capturedUrls.some((u) => u.includes('/api/v2/treatment-plans/tp1')));

    const badUrls = capturedUrls.filter((u) =>
      /\/api\/v2\/clinical\/patients\/.+\/treatment-plans/.test(u),
    );
    expect(badUrls).toHaveLength(0);
  });
});
