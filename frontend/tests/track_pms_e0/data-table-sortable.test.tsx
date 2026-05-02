import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DataTable } from '../../src/components/ui/data-table';
import { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<{ total: number }>[] = [
  { accessorKey: 'total', header: 'Total', enableSorting: true },
];
const data = [{ total: 1 }, { total: 3 }, { total: 2 }];

describe('DataTable sortable', () => {
  it('clicking header reorders rows', () => {
    render(<DataTable columns={columns} data={data} />);

    const header = screen.getByText('Total');
    // First click: sort desc
    fireEvent.click(header);
    const afterFirst = screen.getAllByRole('cell').map((c) => c.textContent);
    expect(afterFirst).toEqual(['3', '2', '1']);

    // Second click: sort asc
    fireEvent.click(header);
    const afterSecond = screen.getAllByRole('cell').map((c) => c.textContent);
    expect(afterSecond).toEqual(['1', '2', '3']);
  });
});
