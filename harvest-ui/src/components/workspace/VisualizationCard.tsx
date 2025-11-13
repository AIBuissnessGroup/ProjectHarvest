"use client"

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GripVertical, Maximize2, Minimize2, X, BarChart3 } from "lucide-react";

interface VisualizationCardProps {
    id: string;
    title: string;
    type: "chart" | "table" | "metric";
    width?: number;
    height?: number;
    onRemove?: () => void;
}

export function VisualizationCard({
    id,
    title,
    type,
    width = 400,
    height = 300,
    onRemove
}: VisualizationCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <Card
            className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 border-slate-700/50 backdrop-blur-sm shadow-xl group relative"
            style={{ width: `${width}px`, height: `${height}px` }}
        >
            {/* Drag Handle */}
            <div className="absolute top-0 left-0 right-0 h-10 bg-slate-800/50 border-b border-slate-700/50 rounded-t-lg flex items-center justify-between px-3 cursor-move opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="flex items-center gap-2">
                    <GripVertical className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-medium text-slate-300">{title}</span>
                </div>
                <div className="flex items-center gap-1">
                    <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 w-6 p-0 hover:bg-slate-700"
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        {isExpanded ? (
                            <Minimize2 className="w-3 h-3 text-slate-400" />
                        ) : (
                            <Maximize2 className="w-3 h-3 text-slate-400" />
                        )}
                    </Button>
                    <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 w-6 p-0 hover:bg-slate-700 hover:text-red-400"
                        onClick={onRemove}
                    >
                        <X className="w-3 h-3" />
                    </Button>
                </div>
            </div>

            {/* Content */}
            <div className="p-6 pt-12 h-full flex items-center justify-center">
                {type === "chart" && (
                    <div className="text-center">
                        <div className="w-16 h-16 bg-gradient-to-br from-brand-500/20 to-brand-600/20 rounded-xl flex items-center justify-center mx-auto mb-3 border border-brand-500/30">
                            <BarChart3 className="w-8 h-8 text-brand-400" />
                        </div>
                        <p className="text-sm text-slate-300 font-medium">Chart Visualization</p>
                        <p className="text-xs text-slate-500 mt-1">{title}</p>
                    </div>
                )}
            </div>

            {/* Resize Handle */}
            <div className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute bottom-1 right-1 w-3 h-3 border-r-2 border-b-2 border-brand-500/50" />
            </div>
        </Card>
    );
}
