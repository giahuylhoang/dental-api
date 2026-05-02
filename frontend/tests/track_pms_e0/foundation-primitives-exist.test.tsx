import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Sheet, SheetContent, SheetTrigger } from '../../src/components/ui/sheet';
import { Separator } from '../../src/components/ui/separator';
import { ScrollArea } from '../../src/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../src/components/ui/tooltip';
import { DataTable } from '../../src/components/ui/data-table';

describe('E0 foundation primitives', () => {
  it('Sheet mounts without crashing', () => {
    render(
      <Sheet>
        <SheetTrigger>open</SheetTrigger>
        <SheetContent>content</SheetContent>
      </Sheet>
    );
    expect(screen.getByText('open')).toBeTruthy();
  });

  it('Separator mounts without crashing', () => {
    const { container } = render(<Separator />);
    expect(container.firstChild).toBeTruthy();
  });

  it('ScrollArea mounts without crashing', () => {
    render(<ScrollArea><div>scroll content</div></ScrollArea>);
    expect(screen.getByText('scroll content')).toBeTruthy();
  });

  it('Tooltip mounts without crashing', () => {
    render(
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>hover me</TooltipTrigger>
          <TooltipContent>tip</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
    expect(screen.getByText('hover me')).toBeTruthy();
  });

  it('DataTable mounts without crashing', () => {
    render(
      <DataTable
        columns={[{ accessorKey: 'name', header: 'Name' }]}
        data={[{ name: 'Alice' }]}
      />
    );
    expect(screen.getByText('Alice')).toBeTruthy();
  });
});
