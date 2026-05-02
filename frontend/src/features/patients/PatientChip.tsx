import { Link } from 'react-router-dom';
import { Skeleton } from '../../components/ui/skeleton';
import { usePatient } from './usePatient';

interface Props {
  patientId?: string | null;
  variant?: 'inline' | 'card' | 'breadcrumb';
  linkTo?: string;
}

function initials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
}

function Avatar({ first, last }: { first: string; last: string }) {
  return (
    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-xs font-medium text-white">
      {initials(first, last)}
    </span>
  );
}

export function PatientChip({ patientId, variant = 'inline', linkTo }: Props) {
  const { patient, isLoading, error } = usePatient(patientId);

  if (!patientId) return null;

  if (isLoading) {
    return <Skeleton className="h-5 w-32" />;
  }

  if (error || !patient) {
    const abbr = `${patientId.slice(0, 2)}…`;
    return (
      <span data-testid="patient-chip" title="Patient not found" className="text-xs text-zinc-400">
        {abbr}
      </span>
    );
  }

  const name = `${patient.first_name} ${patient.last_name}`;
  const href = linkTo ? linkTo.replace(':id', patientId) : undefined;

  let content: React.ReactNode;

  if (variant === 'breadcrumb') {
    content = (
      <span data-testid="patient-chip" className="text-blue-600 hover:underline cursor-pointer">
        {name}
      </span>
    );
  } else if (variant === 'card') {
    content = (
      <span data-testid="patient-chip" className="inline-flex items-center gap-2">
        <Avatar first={patient.first_name} last={patient.last_name} />
        <span className="flex flex-col">
          <span className="font-medium text-sm">{name}</span>
          {patient.phone && <span className="text-xs text-zinc-500">{patient.phone}</span>}
        </span>
      </span>
    );
  } else {
    content = (
      <span data-testid="patient-chip" className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-2 py-0.5 text-xs">
        <Avatar first={patient.first_name} last={patient.last_name} />
        <span>{name}</span>
      </span>
    );
  }

  if (href) {
    return <Link to={href}>{content}</Link>;
  }
  return <>{content}</>;
}
