import { http, HttpResponse } from 'msw';
import { labCasesDb, type MockLabCase } from './lab-cases';
import { treatmentPlansDb } from './treatment-plans';
import { patientsDb } from './patients';

// Seed 12 cases distributed across all 5 statuses with case_number + some with treatment_plan_id
const STATUSES = ['draft', 'sent', 'in_progress', 'returned', 'remake'] as const;

function makeCase(i: number): MockLabCase {
  return {
    id: `lc-f3-${i}`,
    case_number: `LC-2026-${String(i).padStart(4, '0')}`,
    denture_case_id: 'dc1',
    vendor_id: 'v1',
    status: STATUSES[i % STATUSES.length],
    sent_at: null,
    due_back_at: null,
    returned_at: null,
    remake_of_id: null,
    remake_reason: null,
    lab_fee: 300 + i * 50,
    courier_tracking: null,
    clinic_id: 'default',
    treatment_plan_id: i % 3 === 0 ? 'tp1' : null,
  };
}

export const f3SeedCases = Array.from({ length: 12 }, (_, i) => makeCase(i + 1));

// Inject into shared DB (idempotent — only add if not already present)
for (const c of f3SeedCases) {
  if (!labCasesDb.find((x) => x.id === c.id)) labCasesDb.push(c);
}

export const pmsF3Handlers = [
  // POST create lab case (accepts treatment_plan_id)
  http.post('/api/v2/lab/cases', async ({ request }) => {
    const body = (await request.json()) as Partial<MockLabCase>;
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    const idx = labCasesDb.length + 1;
    const newCase: MockLabCase = {
      id: `lc-new-${Date.now()}`,
      case_number: `LC-2026-${String(idx).padStart(4, '0')}`,
      denture_case_id: body.denture_case_id ?? '',
      vendor_id: body.vendor_id ?? '',
      status: 'draft',
      sent_at: null,
      due_back_at: body.due_back_at ?? null,
      returned_at: null,
      remake_of_id: null,
      remake_reason: null,
      lab_fee: body.lab_fee ?? null,
      courier_tracking: null,
      clinic_id: clinicId,
      treatment_plan_id: body.treatment_plan_id ?? null,
    };
    labCasesDb.push(newCase);
    return HttpResponse.json(newCase, { status: 201 });
  }),

  // GET treatment plans (typeahead by patient_id)
  http.get('/api/v2/treatment-plans', ({ request }) => {
    const url = new URL(request.url);
    const patientId = url.searchParams.get('patient_id');
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    const results = (patientId
      ? treatmentPlansDb.filter((p) => p.patient_id === patientId && p.clinic_id === clinicId)
      : treatmentPlansDb.filter((p) => p.clinic_id === clinicId)
    ).map((p) => {
      const patient = patientsDb.find((pt) => pt.id === p.patient_id);
      return { ...p, patient_name: patient ? `${patient.first_name} ${patient.last_name}` : undefined };
    });
    return HttpResponse.json(results);
  }),
];
