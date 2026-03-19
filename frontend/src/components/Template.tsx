'use client';

import { usePathname } from 'next/navigation';
import { Suspense } from 'react';
import dynamic from 'next/dynamic';

const BackgroundScene = dynamic(() => import('./BackgroundScene'), {
  ssr: false,
});

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Ne pas afficher le fond sur la page 3D (home) car elle a déjà sa propre scène
  const showBackground = pathname !== '/home';

  return (
    <>
      {showBackground && (
        <Suspense fallback={null}>
          <BackgroundScene />
        </Suspense>
      )}
      {children}
    </>
  );
}
