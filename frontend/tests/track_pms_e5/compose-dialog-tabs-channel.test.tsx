import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import { ComposeDialog } from '../../src/features/communications/ComposeDialog';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('compose-dialog-tabs-channel', () => {
  it('renders 3 channel tabs: SMS, Email, WhatsApp', async () => {
    server.use(
      http.get('/api/patients', () =>
        HttpResponse.json({ items: [], total: 0, page: 1, limit: 20 }),
      ),
    );

    render(<ComposeDialog onClose={() => {}} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /sms/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /email/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /whatsapp/i })).toBeInTheDocument();
    });
  });

  it('clicking Email tab makes it active (aria-selected=true)', async () => {
    server.use(
      http.get('/api/patients', () =>
        HttpResponse.json({ items: [], total: 0, page: 1, limit: 20 }),
      ),
    );

    render(<ComposeDialog onClose={() => {}} />, { wrapper });

    await waitFor(() => expect(screen.getByRole('tab', { name: /email/i })).toBeInTheDocument());

    const emailTab = screen.getByRole('tab', { name: /email/i });
    // Radix Tabs activates via keyboard in jsdom
    emailTab.focus();
    fireEvent.keyDown(emailTab, { key: 'Enter' });

    await waitFor(() => {
      const tab = screen.getByRole('tab', { name: /email/i });
      expect(tab.getAttribute('aria-selected')).toBe('true');
    });
  });
});
