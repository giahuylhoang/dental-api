"use client";
import { Sidebar } from "@/components/dental/Sidebar";
import { TopBar } from "@/components/dental/TopBar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <TopBar />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
