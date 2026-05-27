import React, { useRef, useState, useLayoutEffect } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { debounce } from "lodash";

interface IProps {
  items: any[]
  renderItem: (item: any, index: number) => React.ReactNode;
  minWidth?: number
  gap?: number
}

const VirtualGrid: React.FC<IProps> = (props) => {
  const { 
    items,
    renderItem,
    minWidth = 200, 
    gap = 16
  } = props;

  const parentRef = useRef<any>(null);

  // 计算当前容器能放几列
  const [columns, setColumns] = useState<number>(1);
  const [rowCount, setRowCount] = useState<number>(0);

  useLayoutEffect(() => {
    if (!parentRef.current)
      return;
    
    const updateColumns = () => {
      if (parentRef.current) {  
        const width = parentRef.current.offsetWidth;
        const cols = Math.max(1, Math.floor(width / (minWidth + gap / 2)));
        setColumns(cols);
        setRowCount(Math.ceil(items.length / cols))
      }
    }
    updateColumns();

    const observer = new window.ResizeObserver(debounce(updateColumns, 50));
    observer.observe(parentRef.current);

    return () => observer.disconnect();
  }, [])

  // 虚拟化行
  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => minWidth + 40, // 估算每行高度
    overscan: 3,
    gap
  });

  return (
    <div
      ref={parentRef}
      className='h-full relative overflow-auto hide-scrollbar'
    >
      <div
        style={{
          height: rowVirtualizer.getTotalSize(),
          position: "relative",
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const rowIndex = virtualRow.index;
          const start = rowIndex * columns;
          const end = Math.min(start + columns, items.length);

          return (
            <div
              key={rowIndex}
              data-index={rowIndex}
              ref={rowVirtualizer.measureElement}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualRow.start}px)`,
                display: "grid",
                gridTemplateColumns: `repeat(${columns}, minmax(${minWidth}px, 1fr))`,
                gap: `${gap}px`
              }}
            >
              {items.slice(start, end).map((item, i) => renderItem(item, start + i))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default VirtualGrid