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

interface ThreatTypeChartProps {
  data: Record<string, number>;
}

const THREAT_COLORS: Record<string, string> = {
  'Confirmed Phishing': '#f43f5e',
  Phishing: '#ef4444',
  'Potential Phishing': '#f97316',
  'Social Engineering': '#a855f7',
  None: '#10b981',
  Clean: '#10b981',
};

export const ThreatTypeChart: React.FC<ThreatTypeChartProps> = ({ data = {} }) => {
  const chartData = Object.entries(data)
    .filter(([_, count]) => count > 0)
    .map(([rawName, count]) => {
      const name = rawName === 'None' ? 'None (Clean)' : rawName;
      return { name, count, originalKey: rawName };
    })
    .sort((a, b) => b.count - a.count);

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-xs italic">
        No active threat signatures or classification data yet
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 10, right: 20, left: 20, bottom: 10 }}
        >
          <XAxis
            type="number"
            allowDecimals={false}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
            width={120}
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
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={THREAT_COLORS[entry.originalKey] || '#818cf8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
