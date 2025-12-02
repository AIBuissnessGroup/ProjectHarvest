"use client"

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Plus, Grid3x3, Sparkles } from "lucide-react";
import { VisualizationCard } from "./VisualizationCard";
import FutureCCUChart from "@/components/charts/FutureCCUChart";
import HistoricalCCUChart from "@/components/charts/HistoricalCCUChart";
import DraggableChart from "./DraggableChart";

interface Visualization {
    id: string;
    type: string;
    data: any;
    position: { x: number; y: number };
    size: { width: number; height: number };
}

interface WorkspaceCanvasProps {
    pageId: string;
    visualizations: Visualization[];
    onRemove: (id: string) => void;
    onPositionChange?: (id: string, position: { x: number; y: number }) => void;
    onSizeChange?: (id: string, size: { width: number; height: number }) => void;
}

export function WorkspaceCanvas({ pageId, visualizations, onRemove, onPositionChange, onSizeChange }: WorkspaceCanvasProps) {
    const canvasRef = useRef<HTMLDivElement>(null);

    // Center the canvas on mount
    useEffect(() => {
        if (canvasRef.current) {
            const container = canvasRef.current;
            const scrollX = (container.scrollWidth - container.clientWidth) / 2;
            const scrollY = (container.scrollHeight - container.clientHeight) / 2;
            container.scrollTo(scrollX, scrollY);
        }
    }, [pageId]); // Re-center when switching pages

    return (
        <div ref={canvasRef} className="workspace-canvas-scroll relative w-full h-full bg-slate-950 overflow-auto">
            {/* Infinite canvas container */}
            <div className="relative" style={{ minWidth: '200%', minHeight: '200%' }}>
                {/* Grid Background */}
                <div
                    className="absolute inset-0 opacity-[0.07] pointer-events-none"
                    style={{
                        backgroundImage: `
                linear-gradient(to right, #14b1e5 1px, transparent 1px),
                linear-gradient(to bottom, #14b1e5 1px, transparent 1px)
              `,
                        backgroundSize: '40px 40px'
                    }}
                />

                {/* Empty State */}
                {visualizations.length === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center max-w-md">
                        <div className="w-20 h-20 bg-gradient-to-br from-brand-500/20 to-brand-600/20 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-brand-500/30 shadow-lg shadow-brand-500/10">
                            <Sparkles className="w-10 h-10 text-brand-400" />
                        </div>
                        <h3 className="text-xl font-semibold text-slate-300 mb-2">Your Canvas Awaits</h3>
                        <p className="text-sm text-slate-400 mb-6">
                            Use the AI assistant to generate visualizations, charts, and insights.
                            They'll appear here where you can drag, resize, and organize them however you like.
                        </p>
                        <div className="flex flex-col gap-2 text-xs text-slate-500">
                            <div className="flex items-center gap-2 justify-center">
                                <Grid3x3 className="w-4 h-4 text-brand-400/50" />
                                <span>Drag and drop to reposition</span>
                            </div>
                            <div className="flex items-center gap-2 justify-center">
                                <Plus className="w-4 h-4 text-brand-400/50" />
                                <span>Resize from corners</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

                {/* Visualizations */}
                {visualizations.map((viz) => {
                    // Future CCU Chart
                    if (viz.type === 'future-ccu-chart' && viz.data?.daily_forecast) {
                        return (
                            <DraggableChart
                                key={viz.id}
                                id={viz.id}
                                initialPosition={viz.position}
                                initialSize={viz.size}
                                onPositionChange={onPositionChange}
                                onSizeChange={onSizeChange}
                                onRemove={onRemove}
                            >
                                <FutureCCUChart
                                    dailyForecast={viz.data.daily_forecast}
                                    baselineCCU={viz.data.baseline_ccu || 0}
                                    currentCCU={viz.data.current_ccu || 0}
                                    mapName={viz.data.map_name}
                                    trend={viz.data.trend}
                                    trendStrength={viz.data.trend_strength}
                                />
                            </DraggableChart>
                        );
                    }
                    
                    // Historical CCU Chart
                    if (viz.type === 'historical-ccu-chart' && viz.data?.historical_data) {
                        return (
                            <DraggableChart
                                key={viz.id}
                                id={viz.id}
                                initialPosition={viz.position}
                                initialSize={viz.size}
                                onPositionChange={onPositionChange}
                                onSizeChange={onSizeChange}
                                onRemove={onRemove}
                            >
                                <HistoricalCCUChart
                                    data={viz.data.historical_data}
                                    mapName={viz.data.map_name}
                                    anomalies={viz.data.anomalies || []}
                                    anomalyCount={viz.data.anomaly_count}
                                />
                            </DraggableChart>
                        );
                    }
                    
                    return null;
                })}
            </div>
        </div>
    );
}
