import { create } from 'zustand';

interface AuthUser {
  id: string;
  clinic_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
  permissions: string[];
}

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  clinicId: string;
  setAuth: (token: string, user: AuthUser) => void;
  setClinicId: (id: string) => void;
  logout: () => void;
}

function loadPersistedAuth(): { accessToken: string | null; user: AuthUser | null } {
  try {
    const token = localStorage.getItem('accessToken');
    const userJson = localStorage.getItem('authUser');
    if (token && userJson) {
      return { accessToken: token, user: JSON.parse(userJson) as AuthUser };
    }
  } catch {
    // ignore
  }
  return { accessToken: null, user: null };
}

const persisted = loadPersistedAuth();

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: persisted.accessToken,
  user: persisted.user,
  clinicId: localStorage.getItem('clinicId') ?? 'default',
  setAuth: (accessToken, user) => {
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('authUser', JSON.stringify(user));
    set({ accessToken, user });
  },
  setClinicId: (clinicId) => {
    localStorage.setItem('clinicId', clinicId);
    set({ clinicId });
  },
  logout: () => {
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('authUser');
    set({ accessToken: null, user: null });
  },
}));
