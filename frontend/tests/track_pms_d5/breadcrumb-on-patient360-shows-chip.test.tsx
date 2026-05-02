import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import AppShell from '../../src/features/shell/AppShell';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter initialEntries={['/patients/p1']}>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('breadcrumb-on-patient360-shows-chip', () => {
  it('shows patient chip in breadcrumb on /patients/:id route', async () => {
    server.use(
      http.get('/api/patients/p1', () =>
        HttpResponse.json({ id: 'p1', first_name: 'Alice', last_name: 'Smith', phone: null, email: null })
      )
    );

    render(<AppShell><div>page</div></AppShell>, { wrapper });

    await waitFor(() => {
      const chip = screen.getByTestId('patient-chip');
      expect(chip).toBeInTheDocument();
      expect(chip.textContent).toContain('Alice');
    });
  });
});
