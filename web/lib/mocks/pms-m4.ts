import { http, HttpResponse } from 'msw';

interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  email: string | null;
  status: string;
  source: string | null;
  notes: string | null;
  owner_id: string | null;
  clinic_id: string;
}

interface Activity {
  id: string;
  kind: string;
  body: string;
  author: string;
  created_at: string;
}

const leadsDb: Lead[] = [
  {
    id: 'L1',
    first_name: 'Alice',
    last_name: 'Smith',
    phone: '555-1234',
    email: 'alice@example.com',
    status: 'NEW',
    source: 'web',
    notes: null,
    owner_id: null,
    clinic_id: 'default',
  },
];

const activitiesDb: Activity[] = [
  {
    id: 'act-1',
    kind: 'note',
    body: 'Initial contact',
    author: 'Dr. Johnson',
    created_at: '2026-05-01T10:00:00Z',
  },
];

export const pmsM4Handlers = [
  http.get('/api/v2/crm/leads', () => HttpResponse.json(leadsDb)),

  http.post('/api/v2/crm/leads', async ({ request }) => {
    const body = (await request.json()) as Partial<Lead>;
    const lead: Lead = {
      id: `lead-${Date.now()}`,
      first_name: body.first_name ?? '',
      last_name: body.last_name ?? '',
      phone: body.phone ?? null,
      email: body.email ?? null,
      status: 'NEW',
      source: body.source ?? null,
      notes: body.notes ?? null,
      owner_id: null,
      clinic_id: 'default',
    };
    leadsDb.push(lead);
    return HttpResponse.json(lead, { status: 201 });
  }),

  http.get('/api/v2/crm/leads/:id', ({ params }) => {
    const lead = leadsDb.find((l) => l.id === params.id);
    if (!lead) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json(lead);
  }),

  http.put('/api/v2/crm/leads/:id', async ({ params, request }) => {
    const body = (await request.json()) as Partial<Lead>;
    const idx = leadsDb.findIndex((l) => l.id === params.id);
    if (idx === -1) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    leadsDb[idx] = { ...leadsDb[idx], ...body };
    return HttpResponse.json(leadsDb[idx]);
  }),

  http.get('/api/v2/crm/leads/:id/activities', () => {
    const acts = activitiesDb.filter(() => true); // all for simplicity
    return HttpResponse.json(acts);
  }),

  http.post('/api/v2/crm/leads/:id/activities', async ({ request }) => {
    const body = (await request.json()) as { kind: string; body: string };
    const act: Activity = {
      id: `act-${Date.now()}`,
      kind: body.kind,
      body: body.body,
      author: 'Current User',
      created_at: new Date().toISOString(),
    };
    activitiesDb.push(act);
    return HttpResponse.json(act, { status: 201 });
  }),

  http.get('/api/providers', () =>
    HttpResponse.json([
      { id: 'prov-1', name: 'Dr. Johnson', is_active: true },
      { id: 'prov-2', name: 'Dr. Lee', is_active: true },
    ]),
  ),
];
