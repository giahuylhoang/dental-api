import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
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

describe('integrations-section-shows-status', () => {
  it('shows enabled/disabled dots for each integration', async () => {
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

    // Wait for page to load, then open Integrations card
    await waitFor(() => expect(screen.getByText('Integrations')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Integrations'));

    await waitFor(() => expect(screen.getByText('SMS')).toBeInTheDocument());

    // SMS enabled, Email disabled, WhatsApp enabled
    const dots = screen.getAllByTestId(/dot-(enabled|disabled)/);
    const smsRow = screen.getByText('SMS').closest('div')!;
    const emailRow = screen.getByText('Email').closest('div')!;
    const waRow = screen.getByText('WhatsApp').closest('div')!;

    expect(smsRow.querySelector('[data-testid="dot-enabled"]')).toBeInTheDocument();
    expect(emailRow.querySelector('[data-testid="dot-disabled"]')).toBeInTheDocument();
    expect(waRow.querySelector('[data-testid="dot-enabled"]')).toBeInTheDocument();

    // Suppress unused variable warning
    void dots;
  });
});
