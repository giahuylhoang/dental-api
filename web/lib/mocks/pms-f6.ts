import { http, HttpResponse } from 'msw';

export interface ClinicSettings {
  display_name: string;
  address: string;
  contact_phone: string;
  timezone: string;
  working_hour_start: string;
  working_hour_end: string;
  booking_notification_email: string;
}

export interface IntegrationsSettings {
  sms: { enabled: boolean };
  email: { enabled: boolean };
  whatsapp: { enabled: boolean };
}

const defaultClinic: ClinicSettings = {
  display_name: 'Smile Co',
  address: '123 Main St',
  contact_phone: '555-0100',
  timezone: 'America/Edmonton',
  working_hour_start: '09:00',
  working_hour_end: '17:00',
  booking_notification_email: 'admin@smileco.com',
};

const defaultIntegrations: IntegrationsSettings = {
  sms: { enabled: true },
  email: { enabled: false },
  whatsapp: { enabled: true },
};

export const pmsF6Handlers = [
  http.get('/api/v2/settings/clinic', () => HttpResponse.json(defaultClinic)),
  http.put('/api/v2/settings/clinic', async ({ request }) => {
    const body = await request.json() as Partial<ClinicSettings>;
    return HttpResponse.json({ ...defaultClinic, ...body });
  }),
  http.get('/api/v2/settings/integrations', () => HttpResponse.json(defaultIntegrations)),
];
