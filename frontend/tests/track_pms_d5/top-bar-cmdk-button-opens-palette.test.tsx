import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import AppShell from '../../src/features/shell/AppShell';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('top-bar-cmdk-button-opens-palette', () => {
  it('clicking Search ⌘K button opens the command palette dialog', async () => {
    render(<AppShell><div>content</div></AppShell>, { wrapper });

    const btn = screen.getByRole('button', { name: /search/i });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });
});
