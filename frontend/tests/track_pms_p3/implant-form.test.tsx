import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import ImplantForm from '../../src/features/lab/ImplantForm';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('ImplantForm', () => {
  it('renders form fields', () => {
    render(<ImplantForm dentureCaseId="dc1" onSaved={vi.fn()} />, { wrapper });
    expect(screen.getByText(/Lot number/i)).toBeInTheDocument();
    expect(screen.getByText(/Surface treatment/i)).toBeInTheDocument();
    expect(screen.getByText(/Abutment type/i)).toBeInTheDocument();
  });

  it('shows validation error when lot_number is empty', async () => {
    render(<ImplantForm dentureCaseId="dc1" onSaved={vi.fn()} />, { wrapper });
    fireEvent.click(screen.getByRole('button', { name: /save implant/i }));
    await waitFor(() =>
      expect(screen.getByText(/Lot number is required/i)).toBeInTheDocument(),
    );
  });

  it('submits correct body when form is valid', async () => {
    let capturedBody: unknown;
    server.use(
      http.post('/api/v2/clinical/denture-cases/dc1/implants', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({ id: 'imp1' }, { status: 201 });
      }),
    );

    const onSaved = vi.fn();
    render(<ImplantForm dentureCaseId="dc1" onSaved={onSaved} />, { wrapper });

    // Fill lot_number by name
    const lotInput = document.querySelector('input[name="lot_number"]') as HTMLInputElement;
    fireEvent.change(lotInput, { target: { value: 'LOT-456' } });

    fireEvent.click(screen.getByRole('button', { name: /save implant/i }));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect((capturedBody as { lot_number: string }).lot_number).toBe('LOT-456');
  });
});
