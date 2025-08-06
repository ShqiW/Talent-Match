import { useEffect } from 'react';

export const useResponsiveLayout = () => {
  useEffect(() => {
    const updateWidth = () => {
      const root = document.documentElement;
      root.style.setProperty('--app-width', `${window.innerWidth}px`);
      root.style.setProperty('--container-width', `${window.innerWidth}px`);
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);

    return () => window.removeEventListener('resize', updateWidth);
  }, []);
}; 