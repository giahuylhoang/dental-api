import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Rockyridge Dental AI',
  description: 'The dental practice OS — sovereign, clinical, calm.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
