import { useAuthStore } from './store';
import { fetcher } from '../../api/client';

export interface LoginCredentials {
  email: string;
  password: string;
}

export async function login(creds: LoginCredentials) {
  const data = await fetcher<{
    access_token: string;
    refresh_token: string;
    user: {
      id: string;
      clinic_id: string;
      email: string;
      full_name: string;
      is_active: boolean;
      roles: string[];
      permissions: string[];
    };
  }>('/api/v2/auth/login', {
    method: 'POST',
    body: JSON.stringify(creds),
  });
  localStorage.setItem('refreshToken', data.refresh_token);
  useAuthStore.getState().setAuth(data.access_token, data.user);
  return data.user;
}

export function useCurrentUser() {
  return useAuthStore((s) => s.user);
}
