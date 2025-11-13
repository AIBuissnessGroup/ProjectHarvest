"use client"

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Plus, Grid3x3, Sparkles } from "lucide-react";
import { VisualizationCard } from "./VisualizationCard";

interface Visualization {
    id: string;
    title: string;
    type: "chart" | "table" | "metric";
    x: number;
    y: number;
}

interface WorkspaceCanvasProps {
    pageId: string;
}

export function WorkspaceCanvas({ pageId }: WorkspaceCanvasProps) {
    const [visualizations, setVisualizations] = useState<Visualization[]>([]);

    const handleRemove = (id: string) => {
        setVisualizations(prev => prev.filter(v => v.id !== id));
    };

    return (
        <div className="relative w-full h-full bg-slate-950">
            {/* Grid Background */}
            <div
                className="absolute inset-0 opacity-[0.07]"
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
                <div className="absolute inset-0 flex items-center justify-center">
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
            <div className="absolute inset-0 p-8">
                {visualizations.map((viz) => (
                    <div
                        key={viz.id}
                        className="absolute"
                        style={{ left: viz.x, top: viz.y }}
                    >
                        <VisualizationCard
                            id={viz.id}
                            title={viz.title}
                            type={viz.type}
                            onRemove={() => handleRemove(viz.id)}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
