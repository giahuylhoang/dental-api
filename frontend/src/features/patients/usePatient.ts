import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';

export interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  email?: string | null;
  date_of_birth?: string | null;
  status?: string;
}

export function usePatient(id?: string | null): {
  patient: Patient | null;
  isLoading: boolean;
  error: Error | null;
} {
  const { data, isLoading, error } = useQuery<Patient, Error>({
    queryKey: ['patient', id],
    queryFn: () => fetcher<Patient>(`/api/patients/${id}`),
    enabled: !!id,
    staleTime: Infinity,
  });

  if (!id) return { patient: null, isLoading: false, error: null };
  return { patient: data ?? null, isLoading, error: error ?? null };
}
