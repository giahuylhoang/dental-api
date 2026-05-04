import { http, HttpResponse } from 'msw';

export interface F5Lead {
  id: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  email: string | null;
  status: string;
  source: string | null;
  notes: string | null;
  owner_id: string | null;
  clinic_id: string;
}

// 15 leads: NEW(5) CONTACTED(4) QUALIFIED(3) CONVERTED(2) LOST(1)
const DIST: [string, number][] = [
  ['NEW', 5], ['CONTACTED', 4], ['QUALIFIED', 3], ['CONVERTED', 2], ['LOST', 1],
];
const SOURCES = ['phone', 'web', 'referral', 'walk-in', 'other'];

export const f5LeadsDb: F5Lead[] = DIST.flatMap(([status, count], si) =>
  Array.from({ length: count }, (_, i) => ({
    id: `f5-${status.toLowerCase()}-${i}`,
    first_name: `Lead${si * 5 + i}`,
    last_name: 'Test',
    phone: null,
    email: null,
    status,
    source: SOURCES[(si * 5 + i) % SOURCES.length],
    notes: null,
    owner_id: null,
    clinic_id: 'default',
  })),
);

export const pmsF5Handlers = [
  http.get('/api/v2/crm/leads', () => HttpResponse.json(f5LeadsDb)),
];
