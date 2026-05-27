import { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';

interface ResizeConfig {
  minWidth?: number;
  maxWidth?: number;
  minHeight?: number;
  maxHeight?: number;
}

export function useResizable(config: ResizeConfig = {}, enabled: boolean = true) {
  const [isResizing, setIsResizing] = useState(false);
  const [dimensions, setDimensions] = useState({
    width: window.innerWidth / 3,
    height: window.innerHeight,
    top: 0
  });

  const handleMouseMove = useCallback(
    debounce((e: MouseEvent) => {
      if (!isResizing) return;

      setDimensions(prev => {
        const newWidth = window.innerWidth - e.clientX;
        const clampedWidth = Math.min(
          Math.max(config.minWidth || 300, newWidth),
          config.maxWidth || window.innerWidth * 0.8
        );
        return { ...prev, width: clampedWidth };
      });
    }, 16),
    [isResizing, config]
  );

  const handleHeightResize = useCallback((deltaY: number) => {
    setDimensions(prev => {
      const newHeight = prev.height - deltaY;
      const newTop = prev.top + deltaY;
      
      return {
        ...prev,
        height: Math.min(Math.max(config.minHeight || 300, newHeight), config.maxHeight || window.innerHeight),
        top: Math.max(0, newTop)
      };
    });
  }, [config]);

  useEffect(() => {
    if (!enabled || !isResizing) return;

    const handleMouseMove = debounce((e: MouseEvent) => {
      setDimensions(prev => {
        const newWidth = window.innerWidth - e.clientX;
        const clampedWidth = Math.min(
          Math.max(config.minWidth || 300, newWidth),
          config.maxWidth || window.innerWidth * 0.8
        );
        return { ...prev, width: clampedWidth };
      });
    }, 16);

    const handleMouseUp = () => setIsResizing(false);

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      handleMouseMove.cancel();
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, config, enabled]);

  return {
    isResizing,
    setIsResizing,
    dimensions,
    handleHeightResize
  };
} 