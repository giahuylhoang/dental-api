import type { Metadata } from "next";
import "../styles/design-tokens.css";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Rockyridge Dental AI",
  description: "Dental practice management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans bg-background text-foreground" suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
