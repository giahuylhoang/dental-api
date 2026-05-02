import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LeadKanban from '../../src/features/crm/LeadKanban';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('source-pill-rendered', () => {
  it('shows source pill for each lead with different sources', async () => {
    const sources = ['phone', 'web', 'referral', 'walk-in', 'other'];
    const leads = sources.map((source, i) => ({
      id: `src-${i}`,
      first_name: `Lead${i}`,
      last_name: 'Src',
      phone: null,
      email: null,
      status: 'NEW',
      source,
      notes: null,
      owner_id: null,
      clinic_id: 'default',
    }));

    server.use(
      http.get('/api/v2/crm/leads', () => HttpResponse.json(leads)),
    );

    render(<LeadKanban />, { wrapper });

    await waitFor(() => {
      for (const source of sources) {
        expect(screen.getByText(new RegExp(source, 'i'))).toBeInTheDocument();
      }
    });
  });
});
