import { http, HttpResponse } from 'msw';

export const authHandlers = [
  http.post('/api/v2/auth/login', async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    if (body.password !== 'password') {
      return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
    }
    return HttpResponse.json({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      expires_in: 3600,
      user: {
        id: 'mock-admin',
        clinic_id: 'default',
        email: body.email,
        full_name: 'Mock Admin',
        is_active: true,
        roles: ['admin'],
        permissions: ['*.*'],
      },
    });
  }),

  http.post('/api/v2/auth/refresh', () =>
    HttpResponse.json({
      access_token: 'mock-access-token-refreshed',
      refresh_token: 'mock-refresh-token-2',
    }),
  ),

  http.post('/api/v2/auth/logout', () => HttpResponse.json({ ok: true })),

  http.get('/api/v2/auth/me', () =>
    HttpResponse.json({
      id: 'mock-admin',
      clinic_id: 'default',
      email: 'admin@example.com',
      full_name: 'Mock Admin',
      is_active: true,
      roles: ['admin'],
      permissions: ['*.*'],
    }),
  ),
];
