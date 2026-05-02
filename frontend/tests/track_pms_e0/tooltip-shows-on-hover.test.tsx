import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../src/components/ui/tooltip';

describe('Tooltip shows on hover', () => {
  it('shows tooltip content when open', () => {
    render(
      <TooltipProvider>
        <Tooltip open>
          <TooltipTrigger>hover</TooltipTrigger>
          <TooltipContent>info</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );

    expect(screen.getByText('hover')).toBeTruthy();
    expect(screen.getAllByText('info').length).toBeGreaterThan(0);
  });
});
