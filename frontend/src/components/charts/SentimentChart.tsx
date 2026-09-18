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

interface SentimentChartProps {
  data: Record<string, number>;
}

const SENTIMENT_COLORS: Record<string, string> = {
  Negative: '#f43f5e',
  Urgent: '#ef4444',
  Frustration: '#f97316',
  Neutral: '#64748b',
  Positive: '#10b981',
  Satisfaction: '#06b6d4',
};

export const SentimentChart: React.FC<SentimentChartProps> = ({ data = {} }) => {
  const chartData = Object.entries(data)
    .filter(([_, count]) => count > 0)
    .map(([name, count]) => ({
      name,
      count,
    }))
    .sort((a, b) => b.count - a.count);

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-xs italic">
        No sentiment distribution data available
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 15 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
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
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={SENTIMENT_COLORS[entry.name] || '#38bdf8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
