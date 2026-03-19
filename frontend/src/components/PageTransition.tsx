'use client';

import { useEffect, useState, useRef } from 'react';
import { usePathname } from 'next/navigation';

export default function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isVisible, setIsVisible] = useState(false);
  const prevPathname = useRef(pathname);
  const isFirstRender = useRef(true);

  useEffect(() => {
    // Animation initiale au montage
    if (isFirstRender.current) {
      isFirstRender.current = false;
      const timer = setTimeout(() => setIsVisible(true), 50);
      return () => clearTimeout(timer);
    }

    // Animation seulement quand le pathname change (pas quand children change)
    if (pathname !== prevPathname.current) {
      setIsVisible(false);
      prevPathname.current = pathname;

      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 150);

      return () => clearTimeout(timer);
    }
  }, [pathname]);

  return (
    <div
      className={`
        transition-all duration-300 ease-out
        ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
      `}
    >
      {children}
    </div>
  );
}
