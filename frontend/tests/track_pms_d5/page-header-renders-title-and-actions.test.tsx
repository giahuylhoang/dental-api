import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PageHeader } from '../../src/components/ui/page-header';

describe('page-header-renders-title-and-actions', () => {
  it('renders title and actions slot', () => {
    render(
      <PageHeader
        title="Patients"
        actions={<button>X</button>}
      />
    );
    expect(screen.getByText('Patients')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'X' })).toBeInTheDocument();
  });
});
