import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import Scheduler from '../../src/features/scheduling/Scheduler';

// Mock FullCalendar to render a .fc div (jsdom can't run the real calendar)
vi.mock('@fullcalendar/react', () => ({
  default: vi.fn(({ select, eventClick }) => {
    // Store callbacks on window for programmatic triggering in other tests
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

describe('Scheduler renders FullCalendar', () => {
  it('renders a .fc element in the DOM', async () => {
    server.use(
      http.get('/api/calendar/events', () => HttpResponse.json([])),
    );

    render(<Scheduler />, { wrapper });

    const fc = document.querySelector('.fc');
    expect(fc).not.toBeNull();
  });
});
