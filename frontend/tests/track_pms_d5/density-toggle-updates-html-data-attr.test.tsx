import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import SettingsPage from '../../src/features/settings/SettingsPage';

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute('data-density');
});

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('density-toggle-updates-html-data-attr', () => {
  it('changing density to compact updates data-density and localStorage', async () => {
    render(<SettingsPage />, { wrapper });

    const select = await screen.findByRole('combobox', { name: /density/i });
    fireEvent.change(select, { target: { value: 'compact' } });

    await waitFor(() => {
      expect(document.documentElement.getAttribute('data-density')).toBe('compact');
      expect(localStorage.getItem('pms.density')).toBe('compact');
    });
  });
});
