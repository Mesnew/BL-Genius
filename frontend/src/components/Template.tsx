'use client';

import { usePathname } from 'next/navigation';
import SimpleBackground from './SimpleBackground';

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Ne pas afficher le fond sur la page 3D (home) car elle a déjà sa propre scène
  const showBackground = pathname !== '/home';

  return (
    <>
      {showBackground && <SimpleBackground />}
      <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
    </>
  );
}
