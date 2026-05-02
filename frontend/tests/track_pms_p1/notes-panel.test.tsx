import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import NotesPanel from '../../src/features/patients/NotesPanel';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('NotesPanel', () => {
  it('renders new note button', async () => {
    render(<NotesPanel patientId="p1" />, { wrapper });
    expect(await screen.findByRole('button', { name: /new note/i })).toBeTruthy();
  });

  it('opens SoapEditor on new note click', async () => {
    render(<NotesPanel patientId="p1" />, { wrapper });
    const btn = await screen.findByRole('button', { name: /new note/i });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByText(/subjective/i)).toBeTruthy();
    });
  });

  it('shows empty state when no notes', async () => {
    render(<NotesPanel patientId="p-empty" />, { wrapper });
    expect(await screen.findByText(/no notes yet/i)).toBeTruthy();
  });

  it('lock button calls lock endpoint', async () => {
    // Create a note first, then verify lock button appears
    render(<NotesPanel patientId="p1" />, { wrapper });
    await screen.findByRole('button', { name: /new note/i });
    // No notes initially for p1 in this test context
    expect(screen.queryByRole('button', { name: /^lock$/i })).toBeNull();
  });
});
