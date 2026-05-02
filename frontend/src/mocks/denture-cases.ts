import { http, HttpResponse } from 'msw';

export interface MockDentureCase {
  id: string;
  patient_id: string;
  arch: string;
  case_type: string;
  current_stage: string;
  status: string;
  opened_at: string;
  closed_at: string | null;
  notes: string | null;
  clinic_id: string;
}

export interface MockDentureCaseEvent {
  id: string;
  case_id: string;
  stage: string;
  occurred_at: string;
  provider_id: number | null;
  note: string | null;
  photo_document_ids: string[];
}

export const dentureCasesDb: MockDentureCase[] = [
  {
    id: 'dc1',
    patient_id: 'p1',
    arch: 'upper',
    case_type: 'complete',
    current_stage: 'consult',
    status: 'open',
    opened_at: '2026-04-01T09:00:00Z',
    closed_at: null,
    notes: null,
    clinic_id: 'default',
  },
];

export const dentureCaseEventsDb: MockDentureCaseEvent[] = [
  {
    id: 'dce1',
    case_id: 'dc1',
    stage: 'consult',
    occurred_at: '2026-04-01T09:00:00Z',
    provider_id: 1,
    note: 'Initial consultation',
    photo_document_ids: [],
  },
];

const STAGE_ORDER = [
  'consult',
  'prelim_imp',
  'final_imp',
  'bite_reg',
  'wax_tryin',
  'insert',
  'adjust',
  'complete',
];

export const dentureCaseHandlers = [
  http.get('/api/v2/clinical/patients/:patientId/denture-cases', ({ params, request }) => {
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    const cases = dentureCasesDb.filter(
      (c) => c.patient_id === params.patientId && c.clinic_id === clinicId,
    );
    return HttpResponse.json(cases);
  }),

  http.post('/api/v2/clinical/patients/:patientId/denture-cases', async ({ params, request }) => {
    const body = (await request.json()) as Partial<MockDentureCase>;
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    const newCase: MockDentureCase = {
      id: `dc${Date.now()}`,
      patient_id: params.patientId as string,
      arch: body.arch ?? 'upper',
      case_type: body.case_type ?? 'complete',
      current_stage: 'consult',
      status: 'open',
      opened_at: new Date().toISOString(),
      closed_at: null,
      notes: body.notes ?? null,
      clinic_id: clinicId,
    };
    dentureCasesDb.push(newCase);
    return HttpResponse.json(newCase, { status: 201 });
  }),

  http.get('/api/v2/clinical/denture-cases/:caseId/events', ({ params }) => {
    const events = dentureCaseEventsDb.filter((e) => e.case_id === params.caseId);
    return HttpResponse.json(events);
  }),

  http.post('/api/v2/clinical/denture-cases/:caseId/advance', async ({ params, request }) => {
    const body = (await request.json()) as { note?: string; photo_document_ids?: string[] };
    const dc = dentureCasesDb.find((c) => c.id === params.caseId);
    if (!dc) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    const idx = STAGE_ORDER.indexOf(dc.current_stage);
    if (idx === -1 || idx >= STAGE_ORDER.length - 1) {
      return HttpResponse.json({ detail: 'Cannot advance' }, { status: 400 });
    }
    dc.current_stage = STAGE_ORDER[idx + 1];
    if (dc.current_stage === 'complete') dc.status = 'closed';
    const event: MockDentureCaseEvent = {
      id: `dce${Date.now()}`,
      case_id: dc.id,
      stage: dc.current_stage,
      occurred_at: new Date().toISOString(),
      provider_id: null,
      note: body.note ?? null,
      photo_document_ids: body.photo_document_ids ?? [],
    };
    dentureCaseEventsDb.push(event);
    return HttpResponse.json(dc);
  }),
];
