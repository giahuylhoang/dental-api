import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import MedicalForm from '../../src/features/patients/MedicalForm';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('MedicalForm', () => {
  it('renders form fields', async () => {
    render(<MedicalForm patientId="p1" />, { wrapper });
    expect(await screen.findByLabelText(/medical history/i)).toBeTruthy();
    expect(screen.getByLabelText(/allergies/i)).toBeTruthy();
    expect(screen.getByLabelText(/medications/i)).toBeTruthy();
    expect(screen.getByLabelText(/bisphosphonates/i)).toBeTruthy();
  });

  it('submits form and calls POST endpoint', async () => {
    render(<MedicalForm patientId="p1" />, { wrapper });
    const medField = await screen.findByLabelText(/medical history/i);
    fireEvent.change(medField, { target: { value: 'Hypertension' } });

    const saveBtn = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByText(/saved successfully/i)).toBeTruthy();
    });
  });
});
