'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

interface DailyForecast {
  day: number;
  predicted_ccu: number;
  change_from_baseline: number;
  confidence_lower?: number;
  confidence_upper?: number;
}

interface FutureCCUChartProps {
  dailyForecast: DailyForecast[];
  baselineCCU: number;
  currentCCU: number;
  mapName?: string;
  trend?: string;
  trendStrength?: string;
}

export default function FutureCCUChart({
  dailyForecast,
  baselineCCU,
  currentCCU,
  mapName = 'Map',
  trend = 'Unknown',
  trendStrength = 'Unknown',
}: FutureCCUChartProps) {
  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div style={{
        backgroundColor: 'rgba(15, 23, 42, 0.98)',
        border: '1px solid #475569',
        borderRadius: '8px',
        padding: '8px 12px',
        color: '#e2e8f0',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
        pointerEvents: 'none'
      }}>
        <p style={{ margin: 0, fontWeight: 'bold', marginBottom: '4px', color: '#e2e8f0' }}>
          {payload[0].payload.day}
        </p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ margin: 0, fontSize: '13px', color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  };

  // Prepare data for the chart
  const chartData = dailyForecast.map((forecast) => ({
    day: `Day ${forecast.day}`,
    'Predicted CCU': forecast.predicted_ccu,
    'Baseline CCU': Math.round(baselineCCU),
    'Lower Bound': forecast.confidence_lower || forecast.predicted_ccu - 50,
    'Upper Bound': forecast.confidence_upper || forecast.predicted_ccu + 50,
  }));

  // Determine trend color
  const getTrendColor = () => {
    if (trend === 'Growing') return '#10b981'; // green
    if (trend === 'Declining') return '#ef4444'; // red
    return '#6b7280'; // gray
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-lg shadow-xl flex flex-col border border-slate-700/50 backdrop-blur-sm" style={{ padding: '2%', overflow: 'visible' }}>
      {/* Header */}
      <div className="flex-shrink-0" style={{ marginBottom: '2%' }}>
        <h3 className="font-bold text-white" style={{ fontSize: '1.2em' }}>
          7-Day CCU Forecast
        </h3>
        {mapName && (
          <p className="text-slate-400" style={{ fontSize: '0.7em', marginTop: '0.5%' }}>
            {mapName}
          </p>
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 flex-shrink-0" style={{ gap: '2%', marginBottom: '2%' }}>
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg" style={{ padding: '3%' }}>
          <p className="text-slate-500 uppercase tracking-wide" style={{ fontSize: '0.55em' }}>
            Current CCU
          </p>
          <p className="font-bold text-white" style={{ fontSize: '1.3em', marginTop: '2%' }}>
            {currentCCU}
          </p>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg" style={{ padding: '3%' }}>
          <p className="text-slate-500 uppercase tracking-wide" style={{ fontSize: '0.55em' }}>
            Baseline (7d Avg)
          </p>
          <p className="font-bold text-white" style={{ fontSize: '1.3em', marginTop: '2%' }}>
            {Math.round(baselineCCU)}
          </p>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg" style={{ padding: '3%' }}>
          <p className="text-slate-500 uppercase tracking-wide" style={{ fontSize: '0.55em' }}>
            Trend
          </p>
          <p
            className="font-bold"
            style={{ fontSize: '1.3em', marginTop: '2%', color: getTrendColor() }}
          >
            {trend}
          </p>
          <p className="text-slate-500" style={{ fontSize: '0.55em', marginTop: '2%' }}>
            {trendStrength}
          </p>
        </div>
      </div>

      {/* Chart - takes remaining space */}
      <div className="flex-1 min-h-0 relative overflow-visible">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="day"
              stroke="#94a3b8"
              style={{ fontSize: '0.7em' }}
            />
            <YAxis
              stroke="#94a3b8"
              style={{ fontSize: '0.7em' }}
              label={{
                value: 'CCU',
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: '0.8em', fill: '#94a3b8' },
              }}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: '#3b82f6', strokeWidth: 1, strokeDasharray: '5 5' }}
              wrapperStyle={{ zIndex: 9999 }}
              offset={20}
            />
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />

            {/* Confidence interval area */}
            <Area
              type="monotone"
              dataKey="Upper Bound"
              stroke="#64748b"
              strokeWidth={1}
              strokeDasharray="3 3"
              fill="url(#colorConfidence)"
              fillOpacity={1}
            />
            <Area
              type="monotone"
              dataKey="Lower Bound"
              stroke="#64748b"
              strokeWidth={1}
              strokeDasharray="3 3"
              fill="url(#colorConfidence)"
              fillOpacity={1}
            />

            {/* Baseline line */}
            <Line
              type="monotone"
              dataKey="Baseline CCU"
              stroke="#22c55e"
              strokeWidth={2}
              strokeDasharray="8 4"
              dot={false}
            />

            {/* Predicted CCU line */}
            <Line
              type="monotone"
              dataKey="Predicted CCU"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', r: 5 }}
              activeDot={{ r: 7 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}

