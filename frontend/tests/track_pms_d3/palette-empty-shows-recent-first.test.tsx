import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import CommandPalette from '../../src/features/search/CommandPalette';

beforeEach(() => localStorage.clear());

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('palette-empty-shows-recent-first', () => {
  it('shows Recently viewed before Quick actions and fires no search request when empty', async () => {
    let searchFired = false;
    server.use(
      http.get('/api/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q');
        if (q) searchFired = true;
        return HttpResponse.json({ items: [], total: 0 });
      }),
    );

    localStorage.setItem(
      'pms.recentlyViewed',
      JSON.stringify([{ kind: 'patient', id: 'p1', label: 'Alice', visitedAt: Date.now() }]),
    );

    render(<CommandPalette />, { wrapper });
    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    // Both sections visible
    expect(screen.getByText('Recently viewed')).toBeInTheDocument();
    expect(screen.getByText('Quick actions')).toBeInTheDocument();

    // Recently viewed appears before Quick actions in DOM
    const recentEl = screen.getByText('Recently viewed');
    const quickEl = screen.getByText('Quick actions');
    expect(
      recentEl.compareDocumentPosition(quickEl) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    // No search request fired
    expect(searchFired).toBe(false);
  });
});
