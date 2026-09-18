import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';

interface RiskBarChartProps {
  data: Record<string, number>;
}

const RISK_COLORS: Record<string, string> = {
  Critical: '#f43f5e',
  High: '#f97316',
  Medium: '#eab308',
  Low: '#0ea5e9',
  Safe: '#10b981',
};

export const RiskBarChart: React.FC<RiskBarChartProps> = ({ data }) => {
  const riskOrder = ['Critical', 'High', 'Medium', 'Low', 'Safe'];
  const chartData = riskOrder.map((key) => ({
    name: key,
    count: data[key] || 0,
  }));

  const hasData = chartData.some((d) => d.count > 0);
  if (!hasData) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-sm italic">
        No risk distribution data available
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#1e293b',
              borderRadius: '8px',
              color: '#f8fafc',
            }}
          />
          <Bar dataKey="count" radius={[6, 6, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={RISK_COLORS[entry.name] || '#64748b'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
