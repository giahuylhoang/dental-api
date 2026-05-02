import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Patient360 from '../../src/features/patients/Patient360';

function renderPatient360(patientId = 'p1') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/patients/${patientId}`]}>
        <Routes>
          <Route path="/patients/:id" element={<Patient360 />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Patient360', () => {
  it('renders patient name after loading', async () => {
    renderPatient360('p1');
    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());
  });

  it('renders all tabs', async () => {
    renderPatient360('p1');
    await waitFor(() => screen.getByText('Alice Smith'));
    const tabs = [
      'Overview', 'Medical', 'Insurance', 'Documents',
      'Treatment Plans', 'Denture Cases', 'Notes', 'Appointments',
      'Invoices', 'Communications',
    ];
    for (const tab of tabs) {
      expect(screen.getByRole('button', { name: tab })).toBeInTheDocument();
    }
  });

  it('switching to Appointments tab triggers appointments query', async () => {
    renderPatient360('p1');
    await waitFor(() => screen.getByText('Alice Smith'));
    fireEvent.click(screen.getByRole('button', { name: 'Appointments' }));
    await waitFor(() => {
      const items = screen.queryAllByText(/No appointments|scheduled|2026-05-10/);
      expect(items.length).toBeGreaterThan(0);
    });
  });

  it('switching to Treatment Plans tab shows plans', async () => {
    renderPatient360('p1');
    await waitFor(() => screen.getByText('Alice Smith'));
    fireEvent.click(screen.getByRole('button', { name: 'Treatment Plans' }));
    await waitFor(() =>
      expect(screen.getByText(/Plan #tp1/)).toBeInTheDocument(),
    );
  });

  it('switching to Denture Cases tab shows cases', async () => {
    renderPatient360('p1');
    await waitFor(() => screen.getByText('Alice Smith'));
    fireEvent.click(screen.getByRole('button', { name: 'Denture Cases' }));
    await waitFor(() =>
      expect(screen.getByText(/upper/)).toBeInTheDocument(),
    );
  });
});
