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

describe('settings-density-toggle-uses-switch', () => {
  it('Density section has a select/switch primitive with current value', async () => {
    render(<SettingsPage />, { wrapper });

    // Navigate to Density section
    const densityBtn = await screen.findByRole('button', { name: /^density$/i });
    fireEvent.click(densityBtn);

    // Should show a density control (select = combobox role)
    const control = await screen.findByRole('combobox', { name: /density/i });
    expect(control).toBeInTheDocument();
    // Default value is 'comfortable'
    expect((control as HTMLSelectElement).value).toBe('comfortable');
  });

  it('changing density in Density section updates data-density', async () => {
    render(<SettingsPage />, { wrapper });

    const densityBtn = await screen.findByRole('button', { name: /^density$/i });
    fireEvent.click(densityBtn);

    const control = await screen.findByRole('combobox', { name: /density/i });
    fireEvent.change(control, { target: { value: 'compact' } });

    await waitFor(() => {
      expect(document.documentElement.getAttribute('data-density')).toBe('compact');
      expect(localStorage.getItem('pms.density')).toBe('compact');
    });
  });
});
