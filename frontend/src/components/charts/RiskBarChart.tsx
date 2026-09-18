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
  High: '#ef4444',
  Medium: '#f59e0b',
  Low: '#10b981',
  Safe: '#38bdf8',
};

export const RiskBarChart: React.FC<RiskBarChartProps> = ({ data = {} }) => {
  const riskOrder = ['Critical', 'High', 'Medium', 'Low', 'Safe'];

  // Case-insensitive lookup
  const getCount = (name: string) => {
    return (
      data[name] ||
      data[name.toLowerCase()] ||
      data[name.toUpperCase()] ||
      data[name.charAt(0).toUpperCase() + name.slice(1).toLowerCase()] ||
      0
    );
  };

  const chartData = riskOrder.map((key) => ({
    name: key,
    count: getCount(key),
  }));

  const hasData = chartData.some((d) => d.count > 0);
  if (!hasData) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-xs italic">
        No risk distribution data available
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 15 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 500 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '12px',
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
