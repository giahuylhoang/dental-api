import Link from "next/link";

export interface LockedFeatureProps {
  title: string;
  body: string;
  backHref: string;
  backLabel?: string;
}

export function LockedFeature({ title, body, backHref, backLabel = "Back" }: LockedFeatureProps) {
  return (
    <section className="bg-card text-card-foreground border border-border rounded-lg shadow-md p-8 max-w-2xl">
      <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
        Engineering Decision: Locked
      </span>
      <h2 className="mt-3 font-display text-2xl">{title}</h2>
      <p className="mt-3 text-muted-foreground max-w-prose">{body}</p>
      <Link
        href={backHref}
        className="mt-6 inline-flex items-center text-sm text-primary hover:underline"
      >
        ← {backLabel}
      </Link>
    </section>
  );
}
