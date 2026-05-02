import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppShell from './features/shell/AppShell';
import LoginPage from './features/auth/LoginPage';
import { Authed } from './features/auth/guards';
import PatientList from './features/patients/PatientList';
import Patient360 from './features/patients/Patient360';
import LabCaseKanban from './features/lab/LabCaseKanban';

const queryClient = new QueryClient();

function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h2 className="mb-2 text-2xl font-semibold">{title}</h2>
      <p className="text-sm text-zinc-600">Coming soon.</p>
    </div>
  );
}

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
                    <Route path="/" element={<Navigate to="/patients" replace />} />
                    <Route path="/patients" element={<PatientList />} />
                    <Route path="/patients/:id" element={<Patient360 />} />
                    <Route path="/lab" element={<LabCaseKanban />} />
                    <Route path="/schedule" element={<Placeholder title="Schedule" />} />
                    <Route path="/plans" element={<Placeholder title="Treatment Plans" />} />
                    <Route path="/crm" element={<Placeholder title="CRM" />} />
                    <Route path="/billing" element={<Placeholder title="Billing" />} />
                    <Route path="/settings" element={<Placeholder title="Settings" />} />
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
