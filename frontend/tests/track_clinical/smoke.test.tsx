import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from '../../src/App';

describe('track-4 smoke', () => {
  it('renders the login page when unauthenticated', () => {
    render(<App />);
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
  });
});
