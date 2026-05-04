export default function PortalLayout({ children }: { children: React.ReactNode }) {
  return <div className="dark min-h-screen bg-background text-foreground">{children}</div>;
}
