import { useAuthStore } from '@/lib/auth/store';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

async function refreshAccessToken(): Promise<string | null> {
  const rt = typeof window !== 'undefined' ? localStorage.getItem('refreshToken') : null;
  if (!rt) return null;
  const res = await fetch(`${BASE}/api/v2/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: rt }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access_token: string; refresh_token: string };
  if (typeof window !== 'undefined') localStorage.setItem('refreshToken', data.refresh_token);
  useAuthStore.getState().setAuth(data.access_token, useAuthStore.getState().user!);
  return data.access_token;
}

export async function fetcher<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { accessToken, clinicId } = useAuthStore.getState();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Clinic-Id': clinicId,
    ...(init.headers as Record<string, string>),
  };
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;

  let res = await fetch(`${BASE}${path}`, { ...init, headers });

  if (res.status === 401 && accessToken) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`;
      res = await fetch(`${BASE}${path}`, { ...init, headers });
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail: string }).detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}
