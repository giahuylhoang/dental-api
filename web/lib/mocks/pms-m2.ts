import { http, HttpResponse } from 'msw';

export const pmsM2Handlers = [
  http.post('/api/v2/clinical/documents/upload', async () => {
    return HttpResponse.json(
      {
        id: `doc-${Date.now()}`,
        patient_id: 'p1',
        kind: 'other',
        storage_url: 'https://example.com/doc.pdf',
        size_bytes: 1024,
        created_at: new Date().toISOString(),
      },
      { status: 201 },
    );
  }),
];
