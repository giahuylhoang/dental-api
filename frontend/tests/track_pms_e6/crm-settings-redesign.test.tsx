import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LeadKanban from '../../src/features/crm/LeadKanban';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

const COLUMNS = ['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST'];

describe('crm-settings-redesign', () => {
  it('LeadKanban source has ≥3 ui imports', () => {
    const dir = path.dirname(fileURLToPath(import.meta.url));
    const src = fs.readFileSync(
      path.resolve(dir, '../../src/features/crm/LeadKanban.tsx'),
      'utf8',
    );
    const matches = src.match(/from ['"](?:\.\.\/)+components\/ui|from ['"]@\/components\/ui/g);
    expect((matches ?? []).length).toBeGreaterThanOrEqual(3);
  });

  it('renders PageHeader with title CRM', async () => {
    server.use(
      http.get('/api/v2/crm/leads', () => HttpResponse.json([])),
    );
    render(<LeadKanban />, { wrapper });
    expect(await screen.findByText('CRM')).toBeInTheDocument();
  });

  it('renders all 5 columns', async () => {
    server.use(
      http.get('/api/v2/crm/leads', () => HttpResponse.json([])),
    );
    render(<LeadKanban />, { wrapper });
    // Wait for loading to finish (columns appear after data loads)
    await waitFor(() => {
      for (const col of COLUMNS) {
        expect(screen.getByText(new RegExp(`^${col}`, 'i'))).toBeInTheDocument();
      }
    });
  });

  it('lead cards use Card component class', async () => {
    server.use(
      http.get('/api/v2/crm/leads', () =>
        HttpResponse.json([
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
        ]),
      ),
    );
    const { container } = render(<LeadKanban />, { wrapper });
    await screen.findByText('Alice Smith');
    // Card renders with rounded-lg border class
    const cards = container.querySelectorAll('.rounded-lg.border');
    expect(cards.length).toBeGreaterThan(0);
  });
});
