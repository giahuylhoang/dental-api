'use client';

import React from 'react';

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  React.useEffect(() => {
    document.documentElement.classList.add('dark');
    document.body.style.background = '#060F1E';
    document.body.style.color = '#FAF9F6';
    return () => {
      document.documentElement.classList.remove('dark');
      document.body.style.background = '';
      document.body.style.color = '';
    };
  }, []);

  return <>{children}</>;
}
