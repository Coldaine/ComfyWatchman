import { useEffect } from 'react';
import { debounce } from 'lodash';

export function useMousePosition(enabled: boolean = true) {
  useEffect(() => {
    if (!enabled) return;

    const handleMouseMove = debounce((e: MouseEvent) => {
      document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`);
    }, 16); // ~60fps

    document.addEventListener('mousemove', handleMouseMove);
    return () => {
      handleMouseMove.cancel();
      document.removeEventListener('mousemove', handleMouseMove);
    };
  }, [enabled]);
} 