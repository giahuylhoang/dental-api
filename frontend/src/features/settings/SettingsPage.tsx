import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Separator } from '../../components/ui/separator';
import ClinicInfoCard from './ClinicInfoCard';
import WorkingHoursCard from './WorkingHoursCard';
import NotificationsCard from './NotificationsCard';
import IntegrationsCard from './IntegrationsCard';

type Section = 'clinic-info' | 'working-hours' | 'notifications' | 'integrations' | 'density';

const NAV_ITEMS: { id: Section; label: string }[] = [
  { id: 'clinic-info', label: 'Clinic Info' },
  { id: 'working-hours', label: 'Working Hours' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'integrations', label: 'Integrations' },
  { id: 'density', label: 'Density' },
];

type Density = 'compact' | 'comfortable' | 'spacious';

function useDensity() {
  const [density, setDensityState] = useState<Density>(
    () => (localStorage.getItem('pms.density') as Density) ?? 'comfortable',
  );
  useEffect(() => {
    document.documentElement.setAttribute('data-density', density);
  }, [density]);
  function setDensity(d: Density) {
    localStorage.setItem('pms.density', d);
    document.documentElement.setAttribute('data-density', d);
    setDensityState(d);
  }
  return { density, setDensity };
}

interface ClinicSettings {
  display_name: string;
  address: string;
  contact_phone: string;
  timezone: string;
  working_hour_start: string;
  working_hour_end: string;
  booking_notification_email: string;
}

interface IntegrationsSettings {
  sms: { enabled: boolean };
  email: { enabled: boolean };
  whatsapp: { enabled: boolean };
}

export default function SettingsPage() {
  const [active, setActive] = useState<Section>('clinic-info');
  const { density, setDensity } = useDensity();

  const { data: clinic, isLoading: clinicLoading } = useQuery<ClinicSettings>({
    queryKey: ['settings', 'clinic'],
    queryFn: () => fetcher<ClinicSettings>('/api/v2/settings/clinic'),
  });

  const { data: integrations, isLoading: intLoading } = useQuery<IntegrationsSettings>({
    queryKey: ['settings', 'integrations'],
    queryFn: () => fetcher<IntegrationsSettings>('/api/v2/settings/integrations'),
  });

  if (clinicLoading || intLoading) {
    return <div className="p-4 text-sm text-zinc-500">Loading…</div>;
  }

  if (!clinic || !integrations) return null;

  return (
    <div className="flex min-h-0 gap-0">
      {/* Nav rail */}
      <nav className="w-60 shrink-0 border-r border-zinc-200 p-3">
        <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
          Settings
        </p>
        <Separator className="mb-2" />
        <div className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => (
            <Button
              key={item.id}
              variant="ghost"
              className={`w-full justify-start text-sm ${active === item.id ? 'bg-zinc-100 font-medium text-zinc-900' : 'text-zinc-600'}`}
              onClick={() => setActive(item.id)}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </nav>

      {/* Content panel */}
      <div className="flex-1 p-6">
        {active === 'clinic-info' && (
          <ClinicInfoCard
            defaultValues={{
              display_name: clinic.display_name,
              address: clinic.address,
              contact_phone: clinic.contact_phone,
              timezone: clinic.timezone,
            }}
          />
        )}

        {active === 'working-hours' && (
          <WorkingHoursCard
            defaultValues={{
              working_hour_start: clinic.working_hour_start,
              working_hour_end: clinic.working_hour_end,
            }}
          />
        )}

        {active === 'notifications' && (
          <NotificationsCard
            defaultValues={{
              booking_notification_email: clinic.booking_notification_email,
            }}
          />
        )}

        {active === 'integrations' && (
          <IntegrationsCard integrations={integrations} />
        )}

        {active === 'density' && (
          <Card>
            <CardHeader>
              <h2 className="text-base font-semibold">Density</h2>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div>
                <label className="mb-1 block text-sm text-zinc-600">Display density</label>
                <select
                  aria-label="density"
                  value={density}
                  onChange={(e) => setDensity(e.target.value as Density)}
                  className="rounded border border-zinc-300 px-3 py-1.5 text-sm"
                >
                  <option value="compact">Compact</option>
                  <option value="comfortable">Comfortable</option>
                  <option value="spacious">Spacious</option>
                </select>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
