"use client";

import React from "react";
import Link from "next/link";

export interface KanbanColumn {
  key: string;
  label: string;
  dot?: string;
}

export interface KanbanBoardProps<T> {
  columns: KanbanColumn[];
  cards: T[];
  getColumn: (card: T) => string;
  renderCard: (card: T) => React.ReactNode;
  onCardHref?: (card: T) => string;
}

export function KanbanBoard<T>({ columns, cards, getColumn, renderCard, onCardHref }: KanbanBoardProps<T>) {
  const colCount = columns.length;
  const uid = `kb-${colCount}`;
  return (
    <div>
      <style>{`.${uid} { display: grid; grid-template-columns: repeat(${colCount}, 1fr); gap: 14px; }`}</style>
      <div className={uid}>
        {columns.map((col) => {
          const colCards = cards.filter((c) => getColumn(c) === col.key);
          return (
            <div key={col.key} className="bg-muted border border-border rounded-md p-3 flex flex-col gap-2.5 min-h-[480px]">
              <div className="flex justify-between items-center px-1 pb-1.5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-foreground">
                  {col.dot && <KanbanDot color={col.dot} />}
                  {col.label}
                </div>
                <span className="font-mono text-xs text-muted-foreground px-2 py-0.5 bg-card rounded-full font-semibold">
                  {colCards.length}
                </span>
              </div>
              {colCards.map((card, i) => {
                const href = onCardHref ? onCardHref(card) : null;
                const content = renderCard(card);
                if (href) return <Link key={i} href={href} className="no-underline text-inherit">{content}</Link>;
                return <React.Fragment key={i}>{content}</React.Fragment>;
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function KanbanDot({ color }: { color: string }) {
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} />;
}
