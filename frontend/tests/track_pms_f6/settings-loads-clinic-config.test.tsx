import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import SettingsPage from '../../src/features/settings/SettingsPage';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('settings-loads-clinic-config', () => {
  it('prefills form with data from GET /api/v2/settings/clinic', async () => {
    server.use(
      http.get('/api/v2/settings/clinic', () =>
        HttpResponse.json({
          display_name: 'Smile Co',
          address: '123 Main St',
          contact_phone: '555-0100',
          timezone: 'America/Edmonton',
          working_hour_start: '09:00',
          working_hour_end: '17:00',
          booking_notification_email: 'admin@smileco.com',
        }),
      ),
      http.get('/api/v2/settings/integrations', () =>
        HttpResponse.json({
          sms: { enabled: true },
          email: { enabled: false },
          whatsapp: { enabled: true },
        }),
      ),
    );

    render(<SettingsPage />, { wrapper });

    await waitFor(() =>
      expect(screen.getByDisplayValue('Smile Co')).toBeInTheDocument(),
    );

    expect(screen.getByDisplayValue('America/Edmonton')).toBeInTheDocument();
  });
});
