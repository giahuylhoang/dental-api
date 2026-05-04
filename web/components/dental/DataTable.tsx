"use client";

import { useRouter } from "next/navigation";
import React from "react";

export interface DataTableColumn<T> {
  key: string;
  label: string;
  align?: "left" | "right" | "center";
  width?: string;
  mono?: boolean;
  render?: (row: T) => React.ReactNode;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  onRowHref?: (row: T) => string;
  empty?: React.ReactNode;
}

const ALIGN_CLASS: Record<string, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

export function DataTable<T>({ columns, rows, onRowHref, empty }: DataTableProps<T>) {
  const router = useRouter();

  if (!rows || rows.length === 0) {
    return empty ?? (
      <div className="p-10 text-center text-muted-foreground text-sm">No records found.</div>
    );
  }

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={col.key}
              className={`text-xs font-semibold uppercase tracking-widest text-muted-foreground border-b border-border px-3.5 py-3 ${ALIGN_CLASS[col.align ?? "left"]}`}
            >
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => {
          const href = onRowHref ? onRowHref(row) : null;
          return (
            <tr
              key={i}
              onClick={href ? () => router.push(href) : undefined}
              className={`group ${href ? "cursor-pointer hover:bg-muted/40" : "hover:bg-muted/20"} transition-colors`}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`px-3.5 py-3.5 align-middle ${i < rows.length - 1 ? "border-b border-border" : ""} ${col.mono ? "font-mono text-xs" : ""} ${ALIGN_CLASS[col.align ?? "left"]}`}
                >
                  {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? "")}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
