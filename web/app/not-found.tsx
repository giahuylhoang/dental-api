import Link from "next/link";
import { EmptyState } from "@/components/dental/EmptyState";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="flex flex-col items-center gap-4">
        <EmptyState title="Page not found" body="The page you're looking for doesn't exist." />
        <Link href="/dashboard" className="text-sm text-primary hover:underline">← Back to dashboard</Link>
      </div>
    </div>
  );
}
