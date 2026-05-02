import { http, HttpResponse } from 'msw';

export interface MockTreatmentPlan {
  id: string;
  patient_id: string;
  status: string;
  total_estimate: number;
  insurance_estimate: number;
  patient_estimate: number;
  items: MockTreatmentPlanItem[];
  clinic_id: string;
}

export interface MockTreatmentPlanItem {
  id: string;
  sequence: number;
  procedure_code: string;
  description: string | null;
  fee: number;
  insurance_coverage_pct: number | null;
  completed_at: string | null;
  tooth_number?: number | null;
  care_notes?: string | null;
}

export const treatmentPlansDb: MockTreatmentPlan[] = [
  {
    id: 'tp1',
    patient_id: 'p1',
    status: 'draft',
    total_estimate: 1500,
    insurance_estimate: 750,
    patient_estimate: 750,
    items: [
      { id: 'tpi1', sequence: 1, procedure_code: '31310', description: 'Complete upper denture', fee: 1500, insurance_coverage_pct: 50, completed_at: null },
    ],
    clinic_id: 'default',
  },
  {
    id: 'tp2',
    patient_id: 'p2',
    status: 'presented',
    total_estimate: 800,
    insurance_estimate: 400,
    patient_estimate: 400,
    items: [
      { id: 'tpi2', sequence: 1, procedure_code: '01202', description: 'Periodic Oral Exam', fee: 800, insurance_coverage_pct: 50, completed_at: null },
    ],
    clinic_id: 'default',
  },
  {
    id: 'tp3',
    patient_id: 'p3',
    status: 'accepted',
    total_estimate: 2400,
    insurance_estimate: 1200,
    patient_estimate: 1200,
    items: [
      { id: 'tpi3', sequence: 1, procedure_code: '31320', description: 'Complete lower denture', fee: 2400, insurance_coverage_pct: 50, completed_at: null },
    ],
    clinic_id: 'default',
  },
  {
    id: 'tp4',
    patient_id: 'p3',
    status: 'in_progress',
    total_estimate: 600,
    insurance_estimate: 300,
    patient_estimate: 300,
    items: [
      { id: 'tpi4', sequence: 1, procedure_code: '31410', description: 'Partial upper denture', fee: 600, insurance_coverage_pct: 50, completed_at: null },
    ],
    clinic_id: 'default',
  },
  {
    id: 'tp5',
    patient_id: 'p2',
    status: 'completed',
    total_estimate: 1200,
    insurance_estimate: 600,
    patient_estimate: 600,
    items: [
      { id: 'tpi5', sequence: 1, procedure_code: '31310', description: 'Complete upper denture', fee: 1200, insurance_coverage_pct: 50, completed_at: '2025-01-15T10:00:00Z' },
    ],
    clinic_id: 'default',
  },
  {
    id: 'tp6',
    patient_id: 'p3',
    status: 'declined',
    total_estimate: 3000,
    insurance_estimate: 0,
    patient_estimate: 3000,
    items: [
      { id: 'tpi6', sequence: 1, procedure_code: '31320', description: 'Complete lower denture', fee: 3000, insurance_coverage_pct: 0, completed_at: null },
    ],
    clinic_id: 'default',
  },
];

export const proceduresDb = [
  { id: 'proc1', code: '31310', name: 'Complete Upper Denture', default_fee: 1500, category: 'prosthodontic' },
  { id: 'proc2', code: '31320', name: 'Complete Lower Denture', default_fee: 1400, category: 'prosthodontic' },
  { id: 'proc3', code: '31410', name: 'Partial Upper Denture', default_fee: 1200, category: 'prosthodontic' },
  { id: 'proc4', code: '01202', name: 'Periodic Oral Exam', default_fee: 50, category: 'diagnostic' },
];

export const treatmentPlanHandlers = [
  http.get('/api/v2/clinical/patients/:patientId/treatment-plans', ({ params, request }) => {
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    return HttpResponse.json(
      treatmentPlansDb.filter((p) => p.patient_id === params.patientId && p.clinic_id === clinicId),
    );
  }),

  http.get('/api/v2/treatment-plans/:id', ({ params }) => {
    const tp = treatmentPlansDb.find((p) => p.id === params.id);
    if (!tp) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json(tp);
  }),

  http.post('/api/v2/clinical/patients/:patientId/treatment-plans', async ({ params, request }) => {
    const body = (await request.json()) as Partial<MockTreatmentPlan>;
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    const items = body.items ?? [];
    const subtotal = items.reduce((s, i) => s + i.fee, 0);
    const insuranceEst = items.reduce(
      (s, i) => s + i.fee * ((i.insurance_coverage_pct ?? 0) / 100),
      0,
    );
    const tp: MockTreatmentPlan = {
      id: `tp${Date.now()}`,
      patient_id: params.patientId as string,
      status: 'draft',
      total_estimate: subtotal,
      insurance_estimate: insuranceEst,
      patient_estimate: subtotal - insuranceEst,
      items: items.map((item, idx) => ({ ...item, id: `tpi${Date.now()}${idx}`, sequence: idx + 1, completed_at: null })),
      clinic_id: clinicId,
    };
    treatmentPlansDb.push(tp);
    return HttpResponse.json(tp, { status: 201 });
  }),

  http.patch('/api/v2/treatment-plans/:id/status', async ({ params, request }) => {
    const body = (await request.json()) as { status: string };
    const tp = treatmentPlansDb.find((p) => p.id === params.id);
    if (!tp) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    tp.status = body.status;
    return HttpResponse.json(tp);
  }),

  http.get('/api/v2/clinical/procedures', ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q')?.toLowerCase() ?? '';
    const results = q
      ? proceduresDb.filter(
          (p) => p.code.toLowerCase().includes(q) || p.name.toLowerCase().includes(q),
        )
      : proceduresDb;
    return HttpResponse.json(results);
  }),
];
