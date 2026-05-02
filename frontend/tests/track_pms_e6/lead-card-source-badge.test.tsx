import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
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

const leads = [
  {
    id: 'L1',
    first_name: 'Alice',
    last_name: 'Smith',
    phone: '555-1234',
    email: null,
    status: 'NEW',
    source: 'web',
    notes: null,
    clinic_id: 'default',
  },
  {
    id: 'L2',
    first_name: 'Bob',
    last_name: 'Jones',
    phone: null,
    email: 'bob@example.com',
    status: 'CONTACTED',
    source: 'referral',
    notes: null,
    clinic_id: 'default',
  },
  {
    id: 'L3',
    first_name: 'Carol',
    last_name: 'White',
    phone: '555-9999',
    email: null,
    status: 'QUALIFIED',
    source: 'phone',
    notes: null,
    clinic_id: 'default',
  },
];

describe('lead-card-source-badge', () => {
  it('each lead card shows a source Badge', async () => {
    server.use(
      http.get('/api/v2/crm/leads', () => HttpResponse.json(leads)),
    );
    render(<LeadKanban />, { wrapper });

    // Wait for leads to render
    await screen.findByText('Alice Smith');

    // Each lead should have its source shown as a badge
    expect(screen.getByText('web')).toBeInTheDocument();
    expect(screen.getByText('referral')).toBeInTheDocument();
    expect(screen.getByText('phone')).toBeInTheDocument();
  });
});
