'use client';

import { useState, useRef, useEffect } from 'react';
import { GripVertical, X } from 'lucide-react';

interface DraggableChartProps {
  id: string;
  children: React.ReactNode;
  initialPosition: { x: number; y: number };
  initialSize: { width: number; height: number };
  onPositionChange?: (id: string, position: { x: number; y: number }) => void;
  onSizeChange?: (id: string, size: { width: number; height: number }) => void;
  onRemove?: (id: string) => void;
}

export default function DraggableChart({
  id,
  children,
  initialPosition,
  initialSize,
  onPositionChange,
  onSizeChange,
  onRemove,
}: DraggableChartProps) {
  const [position, setPosition] = useState(initialPosition);
  const [size, setSize] = useState(initialSize);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle drag start
  const handleDragStart = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.resize-handle')) return;
    
    e.preventDefault(); // Prevent text selection
    setIsDragging(true);
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  };

  // Handle resize start
  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent text selection
    e.stopPropagation();
    setIsResizing(true);
  };

  // Handle mouse move (for both drag and resize)
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault(); // Prevent text selection while dragging/resizing
      
      if (isDragging) {
        const newPosition = {
          x: Math.max(0, e.clientX - dragOffset.x),
          y: Math.max(0, e.clientY - dragOffset.y),
        };
        setPosition(newPosition);
      } else if (isResizing && containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const newWidth = e.clientX - rect.left;
        const newHeight = e.clientY - rect.top;
        
        // Clamp to min/max without triggering updates beyond bounds
        // Smaller minimum to fit more charts on screen
        const clampedSize = {
          width: Math.max(300, Math.min(1400, newWidth)),
          height: Math.max(240, Math.min(900, newHeight)),
        };
        
        // Only update if different from current size
        if (clampedSize.width !== size.width || clampedSize.height !== size.height) {
          setSize(clampedSize);
        }
      }
    };

    const handleMouseUp = () => {
      if (isDragging) {
        onPositionChange?.(id, position);
      }
      if (isResizing) {
        onSizeChange?.(id, size);
      }
      setIsDragging(false);
      setIsResizing(false);
    };

    if (isDragging || isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isResizing, dragOffset, id, position, size]);

  return (
    <div
      ref={containerRef}
      className="absolute group"
      style={{
        left: position.x,
        top: position.y,
        width: size.width,
        height: size.height,
        cursor: isDragging ? 'grabbing' : 'default',
      }}
    >
      {/* Drag Handle Bar */}
      <div
        className="absolute top-0 left-0 right-0 h-10 bg-slate-800/80 border-b border-slate-700/50 rounded-t-lg flex items-center justify-between px-3 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity z-10 backdrop-blur-sm"
        onMouseDown={handleDragStart}
      >
        <div className="flex items-center gap-2 pointer-events-none">
          <GripVertical className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-300">7-Day CCU Forecast</span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove?.(id);
          }}
          className="h-6 w-6 flex items-center justify-center rounded hover:bg-red-500/20 hover:text-red-400 text-slate-400 transition-colors pointer-events-auto"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="h-full pt-10" style={{ overflow: 'visible' }}>
        {children}
      </div>

      {/* Resize Handle */}
      <div
        className="resize-handle absolute bottom-0 right-0 w-6 h-6 cursor-se-resize opacity-0 group-hover:opacity-100 transition-opacity z-10"
        onMouseDown={handleResizeStart}
      >
        <div className="absolute bottom-1 right-1 w-4 h-4 border-r-2 border-b-2 border-brand-500/70" />
      </div>

      {/* Resizing indicator */}
      {isResizing && (
        <div className="absolute bottom-2 right-10 bg-slate-800/90 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 pointer-events-none">
          {size.width} × {size.height}
        </div>
      )}
    </div>
  );
}

