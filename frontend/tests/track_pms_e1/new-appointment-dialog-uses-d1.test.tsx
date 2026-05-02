import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import NewAppointmentDialog from '../../src/features/scheduling/NewAppointmentDialog';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('NewAppointmentDialog uses D1 components', () => {
  it('renders with Radix Dialog data-state="open"', () => {
    server.use(
      http.get('/api/doctors', () => HttpResponse.json([{ id: 1, name: 'Dr. Smith' }])),
      http.get('/api/services', () => HttpResponse.json([{ id: 1, name: 'Cleaning' }])),
    );

    render(
      <NewAppointmentDialog
        open={true}
        start="2026-05-10T09:00:00"
        end="2026-05-10T09:30:00"
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
      { wrapper },
    );

    // Radix Dialog sets data-state="open" on the content
    const dialogContent = document.querySelector('[data-state="open"]');
    expect(dialogContent).not.toBeNull();
  });

  it('renders provider select with data-testid', () => {
    server.use(
      http.get('/api/doctors', () => HttpResponse.json([{ id: 1, name: 'Dr. Smith' }])),
      http.get('/api/services', () => HttpResponse.json([{ id: 1, name: 'Cleaning' }])),
    );

    render(
      <NewAppointmentDialog
        open={true}
        start="2026-05-10T09:00:00"
        end="2026-05-10T09:30:00"
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
      { wrapper },
    );

    expect(screen.getByTestId('provider-select')).toBeInTheDocument();
  });

  it('renders New Appointment title', () => {
    server.use(
      http.get('/api/doctors', () => HttpResponse.json([])),
      http.get('/api/services', () => HttpResponse.json([])),
    );

    render(
      <NewAppointmentDialog
        open={true}
        start="2026-05-10T09:00:00"
        end="2026-05-10T09:30:00"
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
      { wrapper },
    );

    expect(screen.getByText('New Appointment')).toBeInTheDocument();
  });
});
