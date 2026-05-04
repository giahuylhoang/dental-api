import { http, HttpResponse } from 'msw';
import { treatmentPlansDb } from './treatment-plans';
import type { MockTreatmentPlan } from './treatment-plans';
import { patientsDb } from './patients';

const STATUS_TRANSITIONS: Record<string, string> = {
  present: 'presented',
  accept: 'accepted',
  decline: 'declined',
  'in-progress': 'in_progress',
  complete: 'completed',
};

export const pmsF4Handlers = [
  // Status transition endpoints: POST /api/v2/treatment-plans/:id/:action
  ...Object.keys(STATUS_TRANSITIONS).map((action) =>
    http.post(`/api/v2/treatment-plans/:id/${action}`, ({ params }) => {
      const tp = treatmentPlansDb.find((p) => p.id === params.id);
      if (!tp) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
      tp.status = STATUS_TRANSITIONS[action];
      return HttpResponse.json(tp);
    }),
  ),

  // POST /api/v2/treatment-plans (create — replaces the old clinical path)
  http.post('/api/v2/treatment-plans', async ({ request }) => {
    const body = (await request.json()) as Partial<MockTreatmentPlan>;
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    const items = body.items ?? [];
    const subtotal = items.reduce((s, i) => s + (i.fee ?? 0), 0);
    const insuranceEst = items.reduce(
      (s, i) => s + (i.fee ?? 0) * ((i.insurance_coverage_pct ?? 0) / 100),
      0,
    );
    const tp: MockTreatmentPlan = {
      id: `tp${Date.now()}`,
      patient_id: body.patient_id ?? '',
      status: 'draft',
      total_estimate: subtotal,
      insurance_estimate: insuranceEst,
      patient_estimate: subtotal - insuranceEst,
      items: items.map((item, idx) => ({
        id: `tpi${Date.now()}${idx}`,
        sequence: idx + 1,
        procedure_code: item.procedure_code ?? '',
        description: item.description ?? null,
        fee: item.fee ?? 0,
        insurance_coverage_pct: item.insurance_coverage_pct ?? null,
        completed_at: null,
        tooth_number: item.tooth_number ?? null,
        care_notes: item.care_notes ?? null,
      })),
      clinic_id: clinicId,
    };
    treatmentPlansDb.push(tp);
    const patient = patientsDb.find((p) => p.id === tp.patient_id);
    return HttpResponse.json(
      { ...tp, patient_name: patient ? `${patient.first_name} ${patient.last_name}` : undefined },
      { status: 201 },
    );
  }),
];
