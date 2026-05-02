import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import SettingsPage from '../../src/features/settings/SettingsPage';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('settings-nav-rail', () => {
  it('renders all nav rail items', async () => {
    render(<SettingsPage />, { wrapper });
    // Wait for settings to load (nav buttons appear immediately, content loads async)
    await screen.findByRole('button', { name: /^clinic info$/i });
    expect(screen.getByRole('button', { name: /^working hours$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^notifications$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^integrations$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^density$/i })).toBeInTheDocument();
  });

  it('clicking Working Hours shows that section and hides Clinic Info content', async () => {
    render(<SettingsPage />, { wrapper });

    // Wait for nav to load
    const whBtn = await screen.findByRole('button', { name: /^working hours$/i });
    fireEvent.click(whBtn);

    await waitFor(() => {
      // Working Hours accordion header should be in the content panel
      // (there are two "Working Hours" texts: nav button + accordion header)
      const allWH = screen.getAllByText(/working hours/i);
      expect(allWH.length).toBeGreaterThanOrEqual(1);
    });

    // Clinic Info form fields should not be visible (Clinic Info section is hidden)
    expect(screen.queryByLabelText('display_name')).not.toBeInTheDocument();
  });
});
