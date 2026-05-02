import { describe, it, expect } from 'vitest';
import { render, waitFor, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import { usePatient } from '../../src/features/patients/usePatient';

const alice = { id: 'p1', first_name: 'Alice', last_name: 'Smith', phone: '555-0101', email: 'alice@example.com', date_of_birth: '1975-03-15', status: 'active', clinic_id: 'default' };

let fetchCount = 0;

function setup() {
  fetchCount = 0;
  server.use(
    http.get('/api/patients/:id', ({ params }) => {
      if (params.id === 'p1') { fetchCount++; return HttpResponse.json(alice); }
      return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    }),
  );
}

function ComponentA() {
  const { patient } = usePatient('p1');
  return <div data-testid="a">{patient ? `${patient.first_name} ${patient.last_name}` : ''}</div>;
}

function ComponentB() {
  const { patient } = usePatient('p1');
  return <div data-testid="b">{patient ? `${patient.first_name} ${patient.last_name}` : ''}</div>;
}

function NullComponent() {
  const { patient } = usePatient(null);
  return <div data-testid="null">{patient === null ? 'null' : 'not-null'}</div>;
}

describe('usePatient hook', () => {
  it('two components sharing same id fire GET only once', async () => {
    setup();
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={qc}>
        <ComponentA />
        <ComponentB />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('a')).toHaveTextContent('Alice Smith'));
    await waitFor(() => expect(screen.getByTestId('b')).toHaveTextContent('Alice Smith'));
    expect(fetchCount).toBe(1);
  });

  it('returns null state when id is falsy', () => {
    const qc = new QueryClient();
    render(<QueryClientProvider client={qc}><NullComponent /></QueryClientProvider>);
    expect(screen.getByTestId('null')).toHaveTextContent('null');
  });
});
