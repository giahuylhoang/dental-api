import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import ClinicInfoCard from './ClinicInfoCard';
import WorkingHoursCard from './WorkingHoursCard';
import NotificationsCard from './NotificationsCard';
import IntegrationsCard from './IntegrationsCard';

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
    <div className="mx-auto max-w-2xl space-y-4 p-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <ClinicInfoCard
        defaultValues={{
          display_name: clinic.display_name,
          address: clinic.address,
          contact_phone: clinic.contact_phone,
          timezone: clinic.timezone,
        }}
      />
      <WorkingHoursCard
        defaultValues={{
          working_hour_start: clinic.working_hour_start,
          working_hour_end: clinic.working_hour_end,
        }}
      />
      <NotificationsCard
        defaultValues={{
          booking_notification_email: clinic.booking_notification_email,
        }}
      />
      <IntegrationsCard integrations={integrations} />
    </div>
  );
}
