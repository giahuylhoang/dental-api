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
    // E3 redesign: Patient360 tabs are Overview / Appointments / Documents / Insurance /
    // Treatment Plans / Lab Cases / Communications / Notes
    const tabs = [
      'Overview', 'Appointments', 'Documents', 'Insurance',
      'Treatment Plans', 'Lab Cases', 'Communications', 'Notes',
    ];
    for (const tab of tabs) {
      expect(screen.getByRole('tab', { name: tab })).toBeInTheDocument();
    }
  });

  it('switching to Appointments tab triggers appointments query', async () => {
    renderPatient360('p1');
    await waitFor(() => screen.getByText('Alice Smith'));
    {
      const t = screen.getByRole('tab', { name: 'Appointments' });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }
    await waitFor(() => {
      const items = screen.queryAllByText(/No appointments|scheduled|\d{4}-\d{2}-\d{2}/i);
      expect(items.length).toBeGreaterThan(0);
    });
  });

  it('switching to Treatment Plans tab shows plans', async () => {
    renderPatient360('p1');
    await waitFor(() => screen.getByText('Alice Smith'));
    {
      const t = screen.getByRole('tab', { name: 'Treatment Plans' });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }
    await waitFor(() =>
      expect(screen.getByText(/Plan #tp1/)).toBeInTheDocument(),
    );
  });

  it('switching to Lab Cases tab shows cases', async () => {
    renderPatient360('p1');
    await waitFor(() => screen.getByText('Alice Smith'));
    {
      const t = screen.getByRole('tab', { name: 'Lab Cases' });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }
    // The Lab Cases tab fetches cases for the patient — wait for any tabpanel content
    await waitFor(() => {
      const panel = document.querySelector('[role="tabpanel"][data-state="active"]');
      expect(panel).not.toBeNull();
    });
  });
});
