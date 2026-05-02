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

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  clinicId: localStorage.getItem('clinicId') ?? 'default',
  setAuth: (accessToken, user) => set({ accessToken, user }),
  setClinicId: (clinicId) => {
    localStorage.setItem('clinicId', clinicId);
    set({ clinicId });
  },
  logout: () => {
    localStorage.removeItem('refreshToken');
    set({ accessToken: null, user: null });
  },
}));
