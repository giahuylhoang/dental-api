import { http, HttpResponse } from 'msw';
import { labCasesDb, labVendorsDb } from './lab-cases';
import { dentureCasesDb } from './denture-cases';

interface MockImplant {
  id: string;
  denture_case_id: string;
  tooth_position: number;
  vendor: string;
  model: string | null;
  lot_number: string;
  surface_treatment: string;
  abutment_type: string;
  placed_date: string | null;
}

interface MockMaterial {
  id: string;
  lab_case_id: string;
  item_id: string;
  lot_id: string;
  qty_consumed: number;
  unit_cost: number;
}

const implantsDb: MockImplant[] = [];
const materialsDb: MockMaterial[] = [];

export const pmsP3Handlers = [
  // GET single denture case
  http.get('/api/v2/clinical/denture-cases/:caseId', ({ params }) => {
    const dc = dentureCasesDb.find((c) => c.id === params.caseId);
    if (!dc) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json(dc);
  }),

  // POST close denture case
  http.post('/api/v2/clinical/denture-cases/:caseId/close', ({ params }) => {
    const dc = dentureCasesDb.find((c) => c.id === params.caseId);
    if (!dc) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    dc.status = 'closed';
    dc.closed_at = new Date().toISOString();
    return HttpResponse.json(dc);
  }),

  // GET implants for denture case
  http.get('/api/v2/clinical/denture-cases/:caseId/implants', ({ params }) => {
    return HttpResponse.json(implantsDb.filter((i) => i.denture_case_id === params.caseId));
  }),

  // POST implant
  http.post('/api/v2/clinical/denture-cases/:caseId/implants', async ({ params, request }) => {
    const body = (await request.json()) as Omit<MockImplant, 'id' | 'denture_case_id'>;
    const implant: MockImplant = {
      ...body,
      id: `imp${Date.now()}`,
      denture_case_id: params.caseId as string,
      model: body.model ?? null,
      placed_date: body.placed_date ?? null,
    };
    implantsDb.push(implant);
    return HttpResponse.json(implant, { status: 201 });
  }),

  // POST lab case send
  http.post('/api/v2/lab/cases/:id/send', ({ params }) => {
    const lc = labCasesDb.find((c) => c.id === params.id);
    if (!lc) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    lc.status = 'sent';
    lc.sent_at = new Date().toISOString();
    return HttpResponse.json(lc);
  }),

  // POST lab case return
  http.post('/api/v2/lab/cases/:id/return', ({ params }) => {
    const lc = labCasesDb.find((c) => c.id === params.id);
    if (!lc) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    lc.status = 'returned';
    lc.returned_at = new Date().toISOString();
    return HttpResponse.json(lc);
  }),

  // POST lab case remake
  http.post('/api/v2/lab/cases/:id/remake', async ({ params, request }) => {
    const body = (await request.json()) as { remake_reason?: string };
    const lc = labCasesDb.find((c) => c.id === params.id);
    if (!lc) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    lc.status = 'remake';
    lc.remake_reason = body.remake_reason ?? null;
    const child = {
      ...lc,
      id: `lc${Date.now()}`,
      status: 'draft' as const,
      remake_of_id: lc.id,
      sent_at: null,
      returned_at: null,
    };
    labCasesDb.push(child);
    return HttpResponse.json(child, { status: 201 });
  }),

  // POST lab case materials
  http.post('/api/v2/lab/cases/:id/materials', async ({ params, request }) => {
    const body = (await request.json()) as Omit<MockMaterial, 'id' | 'lab_case_id'>;
    const mat: MockMaterial = { ...body, id: `mat${Date.now()}`, lab_case_id: params.id as string };
    materialsDb.push(mat);
    return HttpResponse.json(mat, { status: 201 });
  }),

  // GET lab vendors (already in lab-cases.ts but ensure it's here too)
  http.get('/api/v2/lab/vendors', () => HttpResponse.json(labVendorsDb)),
];
