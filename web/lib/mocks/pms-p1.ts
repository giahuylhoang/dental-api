import { http, HttpResponse } from 'msw';

interface MedicalHistory {
  medical_history: string;
  allergies: string;
  medications: string;
  bisphosphonates_use: boolean;
}

interface PatientInsurance {
  id: string;
  carrier: string;
  policy_number: string;
  group_number: string | null;
  holder_name: string;
  holder_relationship: string | null;
  is_primary: boolean;
  assignment_of_benefits: boolean;
}

interface PatientStatus {
  status: string;
  can_promote: boolean;
}

interface ToothEntry {
  tooth_number: number;
  status: string;
  surface_notes: Record<string, string> | null;
}

interface ClinicalNote {
  id: string;
  patient_id: string;
  soap_subjective: string;
  soap_objective: string;
  soap_assessment: string;
  soap_plan: string;
  locked_at: string | null;
  supersedes_id: string | null;
  created_at: string;
  updated_at: string;
}

interface DocumentRecord {
  id: string;
  kind: string;
  storage_url: string;
  content_sha256: string;
  mime: string;
  size_bytes: number;
  created_at: string;
}

// In-memory stores
const medicalHistoryDb: Record<string, MedicalHistory> = {};
const insuranceDb: Record<string, PatientInsurance[]> = {};
const statusDb: Record<string, PatientStatus> = {};
const toothChartDb: Record<string, ToothEntry[]> = {};
const notesDb: Record<string, ClinicalNote[]> = {};
const documentsDb: Record<string, DocumentRecord[]> = {};

let insuranceIdCounter = 1;
let noteIdCounter = 1;
let docIdCounter = 1;

function getStatus(patientId: string): PatientStatus {
  return statusDb[patientId] ?? { status: 'pending', can_promote: true };
}

function getToothChart(patientId: string): ToothEntry[] {
  if (!toothChartDb[patientId]) {
    toothChartDb[patientId] = Array.from({ length: 32 }, (_, i) => ({
      tooth_number: i + 1,
      status: 'present',
      surface_notes: null,
    }));
  }
  return toothChartDb[patientId];
}

export const pmsP1Handlers = [
  // Medical history
  http.get('/api/v2/clinical/patients/:id/medical-history', ({ params }) => {
    const id = params.id as string;
    return HttpResponse.json(
      medicalHistoryDb[id] ?? { medical_history: '', allergies: '', medications: '', bisphosphonates_use: false },
    );
  }),

  http.post('/api/v2/clinical/patients/:id/medical-history', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as MedicalHistory;
    medicalHistoryDb[id] = body;
    return HttpResponse.json(body);
  }),

  // Patient status
  http.get('/api/v2/clinical/patients/:id/status', ({ params }) => {
    return HttpResponse.json(getStatus(params.id as string));
  }),

  http.post('/api/v2/clinical/patients/:id/promote', ({ params }) => {
    const id = params.id as string;
    statusDb[id] = { status: 'active', can_promote: false };
    return HttpResponse.json(statusDb[id]);
  }),

  http.put('/api/v2/clinical/patients/:id/status', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as { status: string };
    statusDb[id] = { status: body.status, can_promote: body.status !== 'active' };
    return HttpResponse.json(statusDb[id]);
  }),

  // Insurance
  http.get('/api/v2/clinical/patients/:id/insurance', ({ params }) => {
    return HttpResponse.json(insuranceDb[params.id as string] ?? []);
  }),

  http.post('/api/v2/clinical/patients/:id/insurance', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as Omit<PatientInsurance, 'id'>;
    const ins: PatientInsurance = { ...body, id: String(insuranceIdCounter++) };
    if (!insuranceDb[id]) insuranceDb[id] = [];
    insuranceDb[id].push(ins);
    return HttpResponse.json(ins);
  }),

  http.put('/api/v2/clinical/patients/:patient_id/insurance/:insurance_id', async ({ params, request }) => {
    const pid = params.patient_id as string;
    const iid = params.insurance_id as string;
    const body = (await request.json()) as Omit<PatientInsurance, 'id'>;
    const list = insuranceDb[pid] ?? [];
    const idx = list.findIndex((x) => x.id === iid);
    if (idx === -1) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    list[idx] = { ...body, id: iid };
    return HttpResponse.json(list[idx]);
  }),

  http.delete('/api/v2/clinical/patients/:patient_id/insurance/:insurance_id', ({ params }) => {
    const pid = params.patient_id as string;
    const iid = params.insurance_id as string;
    if (insuranceDb[pid]) {
      insuranceDb[pid] = insuranceDb[pid].filter((x) => x.id !== iid);
    }
    return new HttpResponse(null, { status: 204 });
  }),

  // Tooth chart
  http.get('/api/v2/clinical/patients/:patient_id/tooth-chart', ({ params }) => {
    return HttpResponse.json(getToothChart(params.patient_id as string));
  }),

  http.post('/api/v2/clinical/patients/:patient_id/tooth-chart', async ({ params, request }) => {
    const pid = params.patient_id as string;
    const entries = (await request.json()) as ToothEntry[];
    const chart = getToothChart(pid);
    for (const entry of entries) {
      const idx = chart.findIndex((e) => e.tooth_number === entry.tooth_number);
      if (idx >= 0) chart[idx] = entry;
    }
    return HttpResponse.json(chart);
  }),

  // Clinical notes
  http.get('/api/v2/clinical/notes', ({ request }) => {
    const url = new URL(request.url);
    const patientId = url.searchParams.get('patient_id');
    if (patientId) {
      return HttpResponse.json(notesDb[patientId] ?? []);
    }
    return HttpResponse.json(Object.values(notesDb).flat());
  }),

  http.post('/api/v2/clinical/notes', async ({ request }) => {
    const body = (await request.json()) as Omit<ClinicalNote, 'id' | 'created_at' | 'updated_at'>;
    const id = body.patient_id;
    const note: ClinicalNote = {
      ...body,
      id: String(noteIdCounter++),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    if (!notesDb[id]) notesDb[id] = [];
    notesDb[id].push(note);
    return HttpResponse.json(note, { status: 201 });
  }),

  http.patch('/api/v2/clinical/notes/:id', async ({ params, request }) => {
    const id = params.id as string;
    const body = (await request.json()) as Partial<ClinicalNote>;
    for (const notes of Object.values(notesDb)) {
      const idx = notes.findIndex((n) => n.id === id);
      if (idx >= 0) {
        notes[idx] = { ...notes[idx], ...body, updated_at: new Date().toISOString() };
        return HttpResponse.json(notes[idx]);
      }
    }
    return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  http.post('/api/v2/clinical/notes/:id/lock', ({ params }) => {
    const id = params.id as string;
    for (const notes of Object.values(notesDb)) {
      const idx = notes.findIndex((n) => n.id === id);
      if (idx >= 0) {
        notes[idx] = { ...notes[idx], locked_at: new Date().toISOString() };
        return HttpResponse.json(notes[idx]);
      }
    }
    return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
  }),

  // Documents
  http.get('/api/v2/clinical/patients/:id/documents', ({ params }) => {
    return HttpResponse.json(documentsDb[params.id as string] ?? []);
  }),

  http.post('/api/v2/clinical/documents/upload', async ({ request }) => {
    const fd = await request.formData();
    const patientId = fd.get('patient_id') as string;
    const kind = fd.get('kind') as string;
    const file = fd.get('file') as File | null;
    const doc: DocumentRecord = {
      id: String(docIdCounter++),
      kind,
      storage_url: `https://storage.example.com/${patientId}/${file?.name ?? 'file'}`,
      content_sha256: 'mock-sha256',
      mime: file?.type ?? 'application/octet-stream',
      size_bytes: file?.size ?? 0,
      created_at: new Date().toISOString(),
    };
    if (!documentsDb[patientId]) documentsDb[patientId] = [];
    documentsDb[patientId].push(doc);
    return HttpResponse.json({
      id: doc.id,
      storage_url: doc.storage_url,
      sha256: doc.content_sha256,
      mime_type: doc.mime,
      size_bytes: doc.size_bytes,
      kind: doc.kind,
      patient_id: patientId,
      deduped: false,
    });
  }),
];
