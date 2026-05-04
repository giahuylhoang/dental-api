import { http, HttpResponse } from 'msw';

export const pmsF1Handlers = [
  http.patch('/api/v2/communications/threads/:thread_key/read', () =>
    HttpResponse.json({ ok: true }),
  ),
];
