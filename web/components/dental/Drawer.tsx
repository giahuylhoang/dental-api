"use client";

import React from "react";
import { X } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";

export interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  width?: string;
  children?: React.ReactNode;
}

export function Drawer({ open, onClose, title, width = "min(560px, 100%)", children }: DrawerProps) {
  const uid = `drawer-${width.replace(/[^a-z0-9]/gi, "")}`;
  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-foreground/40 z-40" onClick={onClose} />
        <style>{`.${uid} { width: ${width}; }`}</style>
        <Dialog.Content
          className={`fixed top-0 bottom-0 right-0 bg-card shadow-xl flex flex-col z-50 outline-none animate-in slide-in-from-right duration-300 ${uid}`}
          aria-describedby={undefined}
        >
          <div className="flex justify-between items-start gap-4 px-7 py-5 border-b border-border">
            <Dialog.Title className="font-display font-bold text-2xl text-foreground tracking-tight">
              {title}
            </Dialog.Title>
            <button onClick={onClose} className="p-1.5 rounded text-muted-foreground hover:bg-muted transition-colors" aria-label="Close">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 px-7 py-5 overflow-y-auto flex flex-col gap-4">
            {children}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
