"use client";
import { QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { useEffect, useState } from "react";
import { makeQueryClient } from "@/lib/query/client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => makeQueryClient());
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
    if (process.env.NEXT_PUBLIC_USE_MSW === "true" && typeof window !== "undefined") {
      import("@/lib/mocks/browser").then(({ worker }) =>
        worker.start({ onUnhandledRequest: "bypass" })
      ).catch(() => {});
    }
  }, []);
  return (
    <QueryClientProvider client={client}>
      <TooltipProvider>
        {children}
        {mounted ? <Toaster /> : null}
      </TooltipProvider>
    </QueryClientProvider>
  );
}
