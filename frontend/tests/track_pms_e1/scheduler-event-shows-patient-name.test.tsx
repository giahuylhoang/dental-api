import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import Scheduler from '../../src/features/scheduling/Scheduler';

// Capture the events prop passed to FullCalendar
let capturedEvents: unknown[] = [];

vi.mock('@fullcalendar/react', () => ({
  default: vi.fn(({ events, select, eventClick }) => {
    capturedEvents = events ?? [];
    if (typeof window !== 'undefined') {
      (window as unknown as Record<string, unknown>)['__fcSelect'] = select;
      (window as unknown as Record<string, unknown>)['__fcEventClick'] = eventClick;
    }
    return (
      <div className="fc" data-testid="fullcalendar">
        {(events as Array<{ title: string }>)?.map((e, i) => (
          <div key={i} data-testid="fc-event">{e.title}</div>
        ))}
      </div>
    );
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

describe('Scheduler event chips show patient name', () => {
  it('event title contains patient first name', async () => {
    server.use(
      http.get('/api/calendar/events', () =>
        HttpResponse.json([
          {
            id: 'ev-1',
            title: 'Cleaning',
            start: '2026-05-10T09:00:00',
            end: '2026-05-10T09:30:00',
            patient_id: 'p-alice',
          },
        ]),
      ),
      http.get('/api/patients', ({ request }) => {
        const url = new URL(request.url);
        const ids = url.searchParams.get('ids');
        if (ids) {
          return HttpResponse.json({
            items: [{ id: 'p-alice', first_name: 'Alice', last_name: 'Smith' }],
            total: 1,
          });
        }
        return HttpResponse.json({ items: [], total: 0 });
      }),
      http.get('/api/patients/:id', ({ params }) => {
        if (params.id === 'p-alice') {
          return HttpResponse.json({ id: 'p-alice', first_name: 'Alice', last_name: 'Smith' });
        }
        return HttpResponse.json(null, { status: 404 });
      }),
      http.get('/api/doctors', () => HttpResponse.json([])),
      http.get('/api/services', () => HttpResponse.json([])),
    );

    render(<Scheduler />, { wrapper });

    await waitFor(() => {
      const eventEls = screen.queryAllByTestId('fc-event');
      const titles = eventEls.map((el) => el.textContent ?? '');
      const hasAlice = titles.some((t) => t.includes('Alice'));
      expect(hasAlice || capturedEvents.some((e) => (e as { title: string }).title?.includes('Alice'))).toBe(true);
    }, { timeout: 3000 });
  });
});
