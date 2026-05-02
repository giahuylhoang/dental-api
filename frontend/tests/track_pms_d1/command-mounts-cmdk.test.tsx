import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Command, CommandInput, CommandList, CommandItem } from '../../src/components/ui/command';

describe('Command mounts cmdk', () => {
  it('renders input and item', () => {
    render(
      <Command>
        <CommandInput placeholder="Search" />
        <CommandList>
          <CommandItem>One</CommandItem>
        </CommandList>
      </Command>
    );
    expect(screen.getByPlaceholderText('Search')).toBeInTheDocument();
    expect(screen.getByText('One')).toBeInTheDocument();
  });
});
