import { http, HttpResponse } from 'msw';
import { treatmentPlansDb } from './treatment-plans';
import type { MockTreatmentPlanItem } from './treatment-plans';

export const pmsM3Handlers = [
  http.patch('/api/v2/treatment-plans/:id/items', async ({ params, request }) => {
    const body = (await request.json()) as { items: Partial<MockTreatmentPlanItem>[] };
    const tp = treatmentPlansDb.find((p) => p.id === params.id);
    if (!tp) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    tp.items = tp.items.map((item, idx) => ({
      ...item,
      ...(body.items[idx] ?? {}),
    }));
    return HttpResponse.json(tp);
  }),
];
