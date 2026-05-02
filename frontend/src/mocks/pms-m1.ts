import { http, HttpResponse } from 'msw';

interface CalEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  patient_id?: string;
  doctor_id?: number;
  service_id?: number;
  chief_complaint?: string;
  notes?: string;
  start_time?: string;
  end_time?: string;
}

const calEventsDb: CalEvent[] = [];

export const pmsM1Handlers = [
  http.get('/api/calendar/events', () => HttpResponse.json(calEventsDb)),

  http.post('/api/calendar/events', async ({ request }) => {
    const body = (await request.json()) as CalEvent;
    const ev: CalEvent = {
      id: `ev-${Date.now()}`,
      title: `Appointment`,
      start: body.start_time ?? (body as unknown as Record<string, string>).start ?? '',
      end: body.end_time ?? (body as unknown as Record<string, string>).end ?? '',
      ...body,
    };
    calEventsDb.push(ev);
    return HttpResponse.json(ev, { status: 201 });
  }),

  http.get('/api/doctors', () =>
    HttpResponse.json([
      { id: 1, name: 'Dr. Johnson' },
      { id: 2, name: 'Dr. Lee' },
    ]),
  ),

  http.get('/api/services', () =>
    HttpResponse.json([
      { id: 1, name: 'Cleaning' },
      { id: 2, name: 'Filling' },
    ]),
  ),

  http.post('/api/v2/clinical/patients/quick-book', async ({ request }) => {
    const body = (await request.json()) as { name: string; phone: string };
    const [first_name, ...rest] = body.name.split(' ');
    return HttpResponse.json(
      {
        id: `qb-${Date.now()}`,
        first_name,
        last_name: rest.join(' ') || '',
        phone: body.phone,
      },
      { status: 201 },
    );
  }),
];
