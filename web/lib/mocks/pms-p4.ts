import { http, HttpResponse } from 'msw';
import { treatmentPlansDb } from './treatment-plans';
import type { MockTreatmentPlan } from './treatment-plans';
import { patientsDb } from './patients';

export const fromPlanInvoicesDb: Record<string, unknown>[] = [];

export const pmsP4Handlers = [
  // GET all treatment plans (across patients)
  http.get('/api/v2/treatment-plans', ({ request }) => {
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    const plans = treatmentPlansDb
      .filter((p) => p.clinic_id === clinicId)
      .map((p) => {
        const patient = patientsDb.find((pt) => pt.id === p.patient_id);
        return {
          ...p,
          patient_name: patient ? `${patient.first_name} ${patient.last_name}` : undefined,
        };
      });
    return HttpResponse.json(plans);
  }),

  // GET /api/v2/patients (v2 version for autocomplete)
  http.get('/api/v2/patients', ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q')?.toLowerCase() ?? '';
    const clinicId = request.headers.get('X-Clinic-Id') ?? 'default';
    let results = patientsDb.filter((p) => p.clinic_id === clinicId);
    if (q) {
      results = results.filter(
        (p) =>
          p.first_name.toLowerCase().includes(q) ||
          p.last_name.toLowerCase().includes(q),
      );
    }
    return HttpResponse.json({ items: results, total: results.length });
  }),

  // POST /api/v2/billing/invoices/from-plan
  http.post('/api/v2/billing/invoices/from-plan', async ({ request }) => {
    const body = (await request.json()) as { treatment_plan_id: string; patient_id: string };
    const tp = treatmentPlansDb.find((p) => p.id === body.treatment_plan_id) as MockTreatmentPlan | undefined;
    const inv = {
      id: `inv-from-plan-${Date.now()}`,
      treatment_plan_id: body.treatment_plan_id,
      patient_id: body.patient_id,
      status: 'draft',
      total: tp?.total_estimate ?? 0,
      created_at: new Date().toISOString(),
    };
    fromPlanInvoicesDb.push(inv);
    return HttpResponse.json(inv, { status: 201 });
  }),
];
