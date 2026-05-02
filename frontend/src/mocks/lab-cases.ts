import { http, HttpResponse } from 'msw';

export interface MockLabCase {
  id: string;
  denture_case_id: string;
  vendor_id: string;
  status: string;
  sent_at: string | null;
  due_back_at: string | null;
  returned_at: string | null;
  remake_of_id: string | null;
  remake_reason: string | null;
  lab_fee: number | null;
  courier_tracking: string | null;
  clinic_id: string;
}

export const labCasesDb: MockLabCase[] = [
  {
    id: 'lc1',
    denture_case_id: 'dc1',
    vendor_id: 'v1',
    status: 'sent',
    sent_at: '2026-04-10T09:00:00Z',
    due_back_at: '2026-04-17T09:00:00Z',
    returned_at: null,
    remake_of_id: null,
    remake_reason: null,
    lab_fee: 350,
    courier_tracking: null,
    clinic_id: 'default',
  },
  {
    id: 'lc2',
    denture_case_id: 'dc1',
    vendor_id: 'v1',
    status: 'in_progress',
    sent_at: '2026-04-12T09:00:00Z',
    due_back_at: '2026-04-19T09:00:00Z',
    returned_at: null,
    remake_of_id: null,
    remake_reason: null,
    lab_fee: 400,
    courier_tracking: null,
    clinic_id: 'default',
  },
];

export const labVendorsDb = [
  { id: 'v1', name: 'Precision Dental Lab', contact_email: 'lab@precision.com', sla_days: 7, is_active: true },
];

export const labCaseHandlers = [
  http.get('/api/v2/lab/cases', ({ request }) => {
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    return HttpResponse.json(labCasesDb.filter((c) => c.clinic_id === clinicId));
  }),

  http.patch('/api/v2/lab/cases/:id/status', async ({ params, request }) => {
    const body = (await request.json()) as { status: string; remake_reason?: string };
    const lc = labCasesDb.find((c) => c.id === params.id);
    if (!lc) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    lc.status = body.status;
    if (body.status === 'returned') lc.returned_at = new Date().toISOString();
    if (body.status === 'remake') {
      lc.remake_reason = body.remake_reason ?? null;
      // create child case
      const child: MockLabCase = {
        ...lc,
        id: `lc${Date.now()}`,
        status: 'draft',
        remake_of_id: lc.id,
        remake_reason: body.remake_reason ?? null,
        sent_at: null,
        returned_at: null,
      };
      labCasesDb.push(child);
    }
    return HttpResponse.json(lc);
  }),

  http.get('/api/v2/lab/vendors', () => HttpResponse.json(labVendorsDb)),
];
