import { describe, it, expect, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import Scheduler from '../../src/features/scheduling/Scheduler';

// Mock FullCalendar — same mock as calendar-renders-fullcalendar.test.tsx
vi.mock('@fullcalendar/react', () => ({
  default: vi.fn(({ select, eventClick }) => {
    if (typeof window !== 'undefined') {
      (window as unknown as Record<string, unknown>)['__fcSelect'] = select;
      (window as unknown as Record<string, unknown>)['__fcEventClick'] = eventClick;
    }
    return <div className="fc" data-testid="fullcalendar" />;
  }),
}));
vi.mock('@fullcalendar/timegrid', () => ({ default: {} }));
vi.mock('@fullcalendar/daygrid', () => ({ default: {} }));
vi.mock('@fullcalendar/interaction', () => ({ default: {} }));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Scheduler select callback opens NewAppointmentDialog', () => {
  it('triggers select → dialog appears with pre-filled start time', async () => {
    server.use(
      http.get('/api/calendar/events', () => HttpResponse.json([])),
      http.get('/api/doctors', () => HttpResponse.json([])),
      http.get('/api/services', () => HttpResponse.json([])),
    );

    render(<Scheduler />, { wrapper });

    // Programmatically trigger the FullCalendar select callback
    const selectFn = (window as unknown as Record<string, unknown>)['__fcSelect'] as (
      arg: { startStr: string; endStr: string },
    ) => void;

    expect(selectFn).toBeDefined();

    const startStr = '2026-05-10T09:00:00';
    const endStr = '2026-05-10T09:30:00';

    act(() => {
      selectFn({ startStr, endStr });
    });

    // Dialog should be visible
    expect(screen.getByText('New Appointment')).toBeInTheDocument();

    // Start time should be pre-filled (datetime-local format: 2026-05-10T09:00)
    const startInput = screen.getByDisplayValue('2026-05-10T09:00') as HTMLInputElement;
    expect(startInput).toBeInTheDocument();
  });
});
