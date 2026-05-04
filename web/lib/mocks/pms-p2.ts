import { http, HttpResponse } from 'msw';

interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: number;
  service_id: number;
  start_time: string;
  end_time: string;
  status: string;
  notes?: string;
  patient_name?: string;
  doctor_name?: string;
  service_name?: string;
}

// Build a date in the current week (Monday) so the calendar always shows it
function currentWeekMonday(): string {
  const d = new Date();
  d.setDate(d.getDate() - d.getDay() + 1); // Monday
  return d.toISOString().slice(0, 10);
}

const mondayDate = currentWeekMonday();

export const appointmentsDb: Record<string, Appointment> = {
  'appt-1': {
    id: 'appt-1',
    patient_id: 'p1',
    doctor_id: 1,
    service_id: 1,
    start_time: `${mondayDate}T10:00:00`,
    end_time: `${mondayDate}T11:00:00`,
    status: 'SCHEDULED',
    patient_name: 'Alice Smith',
    doctor_name: 'Dr. Johnson',
    service_name: 'Cleaning',
  },
  'appt-2': {
    id: 'appt-2',
    patient_id: 'p2',
    doctor_id: 2,
    service_id: 2,
    start_time: `${mondayDate}T14:00:00`,
    end_time: `${mondayDate}T15:00:00`,
    status: 'CONFIRMED',
    patient_name: 'Bob Jones',
    doctor_name: 'Dr. Lee',
    service_name: 'Filling',
  },
};

export const pmsP2Handlers = [
  // List appointments (calendar view — v1 endpoint with start/end params)
  http.get('/api/appointments', ({ request }) => {
    const url = new URL(request.url);
    const patientId = url.searchParams.get('patient_id');
    const start = url.searchParams.get('start');
    const end = url.searchParams.get('end');

    let appts = Object.values(appointmentsDb);

    if (patientId) {
      appts = appts.filter((a) => a.patient_id === patientId);
    } else if (start && end) {
      appts = appts.filter((a) => {
        const d = a.start_time.slice(0, 10);
        return d >= start && d <= end;
      });
    }

    return HttpResponse.json(appts);
  }),

  http.get('/api/appointments/:id', ({ params }) => {
    const appt = appointmentsDb[params.id as string];
    if (!appt) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json(appt);
  }),

  http.put('/api/appointments/:id/status', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as { status: string };
    if (!appointmentsDb[id]) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    appointmentsDb[id] = { ...appointmentsDb[id], status: body.status };
    return HttpResponse.json(appointmentsDb[id]);
  }),

  http.put('/api/appointments/:id/cancel', ({ params }) => {
    const id = params.id as string;
    if (!appointmentsDb[id]) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    appointmentsDb[id] = { ...appointmentsDb[id], status: 'CANCELLED' };
    return HttpResponse.json(appointmentsDb[id]);
  }),

  http.put('/api/appointments/:id/reschedule', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as { start_time: string; end_time: string };
    if (!appointmentsDb[id]) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    appointmentsDb[id] = { ...appointmentsDb[id], ...body };
    return HttpResponse.json(appointmentsDb[id]);
  }),
];
