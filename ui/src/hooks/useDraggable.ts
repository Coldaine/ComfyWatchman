import { useState, useEffect, useCallback } from 'react';

interface Position {
  x: number;
  y: number;
}

interface DragConfig {
  initialX?: number;
  initialY?: number;
  boundaryPadding?: {
    right?: number;
    bottom?: number;
  };
  onClick?: () => void;
}

export function useDraggable(config: DragConfig = {}) {
  const [position, setPosition] = useState<Position>({
    x: config.initialX ?? (window.innerWidth - 160),
    y: config.initialY ?? 20
  });
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [startTime, setStartTime] = useState(0);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const newX = Math.min(
        Math.max(0, e.clientX - dragOffset.x), 
        window.innerWidth - (config.boundaryPadding?.right ?? 100)
      );
      const newY = Math.min(
        Math.max(0, e.clientY - dragOffset.y), 
        window.innerHeight - (config.boundaryPadding?.bottom ?? 40)
      );
      setPosition({ x: newX, y: newY });
    }
  }, [isDragging, dragOffset, config.boundaryPadding]);

  const handleMouseUp = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const moveDistance = Math.sqrt(
        Math.pow(e.clientX - startPos.x, 2) + 
        Math.pow(e.clientY - startPos.y, 2)
      );
      const timeElapsed = Date.now() - startTime;

      // 如果移动距离小于 5px 且时间小于 200ms，则认为是点击
      if (moveDistance < 5 && timeElapsed < 200) {
        config.onClick?.();
      }
    }
    setIsDragging(false);
  }, [isDragging, startPos, startTime, config.onClick]);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    setStartTime(Date.now());
    setStartPos({ x: e.clientX, y: e.clientY });
    
    const buttonRect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - buttonRect.left,
      y: e.clientY - buttonRect.top
    });
  };

  return {
    position,
    isDragging,
    handleMouseDown
  };
} 