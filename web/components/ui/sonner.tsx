"use client";

import { Toaster as SonnerToaster } from 'sonner';

export function Toaster() {
  return (
    <SonnerToaster
      toastOptions={{
        classNames: {
          toast: 'bg-background text-foreground border border-border shadow-md',
          description: 'text-muted-foreground',
          actionButton: 'bg-primary text-primary-foreground',
          cancelButton: 'bg-muted text-muted-foreground',
        },
      }}
    />
  );
}
