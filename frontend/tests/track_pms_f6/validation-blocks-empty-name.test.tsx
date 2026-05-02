import { describe, it, expect, vi } from 'vitest';
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

describe('validation-blocks-empty-name', () => {
  it('shows error and does not PUT when display_name is empty', async () => {
    const putSpy = vi.fn();

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
      http.put('/api/v2/settings/clinic', () => {
        putSpy();
        return HttpResponse.json({});
      }),
    );

    render(<SettingsPage />, { wrapper });

    await waitFor(() => expect(screen.getByDisplayValue('Smile Co')).toBeInTheDocument());

    // Clear display_name
    fireEvent.change(screen.getByLabelText('display_name'), {
      target: { value: '' },
    });

    fireEvent.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument(),
    );

    expect(putSpy).not.toHaveBeenCalled();
  });
});
