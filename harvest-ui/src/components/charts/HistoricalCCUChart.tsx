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
  ReferenceDot,
} from 'recharts';

interface HistoricalDataPoint {
  timestamp: string;
  ccu: number;
  isAnomaly?: boolean;
}

interface HistoricalCCUChartProps {
  data: HistoricalDataPoint[];
  mapName?: string;
  anomalies?: { timestamp: string; ccu: number; index?: number }[];
  anomalyCount?: number;
}

export function HistoricalCCUChart({
  data,
  mapName = 'Map',
  anomalies = [],
  anomalyCount: propAnomalyCount,
}: HistoricalCCUChartProps) {
  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const point = payload[0].payload;
    const isAnomaly = point.isAnomaly;

    return (
      <div style={{
        backgroundColor: 'rgba(15, 23, 42, 0.98)',
        border: isAnomaly ? '1px solid #ef4444' : '1px solid #475569',
        borderRadius: '8px',
        padding: '8px 12px',
        color: '#e2e8f0',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
        pointerEvents: 'none'
      }}>
        <p style={{ margin: 0, fontWeight: 'bold', marginBottom: '4px', color: isAnomaly ? '#ef4444' : '#e2e8f0' }}>
          {isAnomaly ? '🚨 Anomaly Detected' : point.timestamp}
        </p>
        <p style={{ margin: 0, fontSize: '13px', color: '#3b82f6' }}>
          CCU: {point.ccu.toLocaleString()}
        </p>
        {isAnomaly && (
          <p style={{ margin: 0, fontSize: '11px', color: '#f87171', marginTop: '4px' }}>
            Unusual spike detected
          </p>
        )}
      </div>
    );
  };

  // Use anomaly flags from data (set by backend) or match by EXACT index only
  // Don't match by CCU value as multiple points can have the same CCU
  const chartData = data.map((point: any, idx: number) => ({
    ...point,
    isAnomaly: point.isAnomaly || anomalies.some(a => a.index === idx || a.index === point.index)
  }));

  // Use backend count if provided, otherwise count from data
  const anomalyCount = propAnomalyCount ?? chartData.filter((d: any) => d.isAnomaly).length;

  // Calculate stats
  const ccuValues = data.map(d => d.ccu);
  const avgCCU = Math.round(ccuValues.reduce((a, b) => a + b, 0) / ccuValues.length);
  const maxCCU = Math.max(...ccuValues);
  const minCCU = Math.min(...ccuValues);

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-lg shadow-xl flex flex-col border border-slate-700/50 backdrop-blur-sm" style={{ padding: '2%', overflow: 'visible' }}>
      {/* Header */}
      <div className="flex-shrink-0" style={{ marginBottom: '2%' }}>
        <h3 className="font-bold text-white" style={{ fontSize: '1.2em' }}>
          Historical CCU Data
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
            Average CCU
          </p>
          <p className="font-bold text-white" style={{ fontSize: '1.3em', marginTop: '2%' }}>
            {avgCCU.toLocaleString()}
          </p>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg" style={{ padding: '3%' }}>
          <p className="text-slate-500 uppercase tracking-wide" style={{ fontSize: '0.55em' }}>
            Peak CCU
          </p>
          <p className="font-bold text-green-400" style={{ fontSize: '1.3em', marginTop: '2%' }}>
            {maxCCU.toLocaleString()}
          </p>
        </div>
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg" style={{ padding: '3%' }}>
          <p className="text-slate-500 uppercase tracking-wide" style={{ fontSize: '0.55em' }}>
            Anomalies
          </p>
          <p className="font-bold" style={{ fontSize: '1.3em', marginTop: '2%', color: anomalyCount > 0 ? '#ef4444' : '#64748b' }}>
            {anomalyCount}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0 relative overflow-visible">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="timestamp"
              stroke="#94a3b8"
              style={{ fontSize: '0.6em' }}
              tick={{ fill: '#94a3b8' }}
              angle={-45}
              textAnchor="end"
              height={60}
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

            {/* Main CCU line */}
            <Line
              type="monotone"
              dataKey="ccu"
              name="CCU"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={(props: any) => {
                const { cx, cy, payload } = props;
                if (payload.isAnomaly) {
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={6}
                      fill="#ef4444"
                      stroke="#fff"
                      strokeWidth={2}
                    />
                  );
                }
                return (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={3}
                    fill="#3b82f6"
                  />
                );
              }}
              activeDot={{ r: 6, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }}
            />

            {/* Average line */}
            <Line
              type="monotone"
              dataKey={() => avgCCU}
              name="Average"
              stroke="#22c55e"
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend explanation */}
      {anomalyCount > 0 && (
        <div className="flex-shrink-0 mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
          <p className="text-xs text-red-400">
            🚨 <span className="font-semibold">{anomalyCount} anomalies detected</span> - Red dots indicate unusual CCU spikes that may be from campaigns or viral moments.
          </p>
        </div>
      )}
    </div>
  );
}

export default HistoricalCCUChart;

