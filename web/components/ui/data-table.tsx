"use client";

import * as React from 'react';
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from '@tanstack/react-table';
import { cn } from '@/lib/utils';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  onRowClick?: (row: TData) => void;
}

export function DataTable<TData, TValue>({ columns, data, onRowClick }: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [rowSelection, setRowSelection] = React.useState({});

  const table = useReactTable({
    data,
    columns,
    state: { sorting, rowSelection },
    onSortingChange: setSorting,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="rounded-md border">
      <table className="w-full text-sm">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b bg-muted/50">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className={cn(
                    'h-10 px-4 text-left font-medium text-muted-foreground',
                    header.column.getCanSort() && 'cursor-pointer select-none hover:text-foreground'
                  )}
                  onClick={header.column.getToggleSortingHandler()}
                >
                  {header.isPlaceholder ? null : (
                    <span className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' && ' ↑'}
                      {header.column.getIsSorted() === 'desc' && ' ↓'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.length ? (
            table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className={cn('border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted', onRowClick && 'cursor-pointer')}
                data-state={row.getIsSelected() ? 'selected' : undefined}
                onClick={onRowClick ? () => onRowClick(row.original) : undefined}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-2">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                No results.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
