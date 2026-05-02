import { http, HttpResponse } from 'msw';

export interface MockPatient {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  date_of_birth: string | null;
  status: string;
  clinic_id: string;
}

export const patientsDb: MockPatient[] = [
  {
    id: 'p1',
    first_name: 'Alice',
    last_name: 'Smith',
    email: 'alice@example.com',
    phone: '555-0101',
    date_of_birth: '1975-03-15',
    status: 'active',
    clinic_id: 'default',
  },
  {
    id: 'p2',
    first_name: 'Bob',
    last_name: 'Jones',
    email: 'bob@example.com',
    phone: '555-0102',
    date_of_birth: '1960-07-22',
    status: 'active',
    clinic_id: 'default',
  },
  {
    id: 'p3',
    first_name: 'Carol',
    last_name: 'White',
    email: 'carol@example.com',
    phone: '555-0103',
    date_of_birth: '1988-11-05',
    status: 'inactive',
    clinic_id: 'default',
  },
];

export const patientHandlers = [
  http.get('/api/patients', ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q')?.toLowerCase() ?? '';
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    let results = patientsDb.filter((p) => p.clinic_id === clinicId);
    if (q) {
      results = results.filter(
        (p) =>
          p.first_name.toLowerCase().includes(q) ||
          p.last_name.toLowerCase().includes(q) ||
          p.email?.toLowerCase().includes(q) ||
          p.phone?.includes(q),
      );
    }
    const page = parseInt(url.searchParams.get('page') ?? '1');
    const limit = parseInt(url.searchParams.get('limit') ?? '20');
    const start = (page - 1) * limit;
    return HttpResponse.json({
      items: results.slice(start, start + limit),
      total: results.length,
      page,
      limit,
    });
  }),

  http.get('/api/patients/:id', ({ params }) => {
    const p = patientsDb.find((x) => x.id === params.id);
    if (!p) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json(p);
  }),

  http.get('/api/appointments', ({ request }) => {
    const url = new URL(request.url);
    const patientId = url.searchParams.get('patient_id');
    const appts = patientId
      ? [
          {
            id: 'a1',
            patient_id: patientId,
            doctor_id: 1,
            start_time: '2026-05-10T10:00:00',
            end_time: '2026-05-10T11:00:00',
            status: 'scheduled',
            service_id: 1,
          },
        ]
      : [];
    return HttpResponse.json(appts);
  }),
];
