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
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('top-bar-shows-clinic-display-name', () => {
  it('shows clinic display name from API in top bar', async () => {
    server.use(
      http.get('/api/v2/settings/clinic', () =>
        HttpResponse.json({ display_name: 'Demo Dental Clinic' })
      )
    );

    render(<AppShell><div>content</div></AppShell>, { wrapper });

    await waitFor(() =>
      expect(screen.getAllByText('Demo Dental Clinic').length).toBeGreaterThanOrEqual(1)
    );
  });
});
