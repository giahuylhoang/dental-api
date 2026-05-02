import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppShell from './features/shell/AppShell';
import LoginPage from './features/auth/LoginPage';
import { Authed } from './features/auth/guards';
import PatientList from './features/patients/PatientList';
import Patient360 from './features/patients/Patient360';
import LabCaseKanban from './features/lab/LabCaseKanban';
import Scheduler from './features/scheduling/Scheduler';
import InvoiceList from './features/billing/InvoiceList';
import CommInbox from './features/communications/CommInbox';
import LeadKanban from './features/crm/LeadKanban';
import Dashboard from './features/reporting/Dashboard';
import TreatmentPlansPage from './features/treatment-plans/TreatmentPlansPage';
import SettingsPage from './features/settings/SettingsPage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <Authed>
                <AppShell>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/patients" element={<PatientList />} />
                    <Route path="/patients/:id" element={<Patient360 />} />
                    <Route path="/schedule" element={<Scheduler />} />
                    <Route path="/lab" element={<LabCaseKanban />} />
                    <Route path="/billing" element={<InvoiceList />} />
                    <Route path="/communications" element={<CommInbox />} />
                    <Route path="/crm" element={<LeadKanban />} />
                    <Route path="/plans" element={<TreatmentPlansPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                  </Routes>
                </AppShell>
              </Authed>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
