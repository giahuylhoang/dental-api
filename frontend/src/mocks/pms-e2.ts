import { http, HttpResponse } from 'msw';

export const pmsE2Handlers = [
  http.get('/api/leads', () => HttpResponse.json([])),
];
