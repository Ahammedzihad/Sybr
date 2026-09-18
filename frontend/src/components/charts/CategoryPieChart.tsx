import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';

interface CategoryPieChartProps {
  data: Record<string, number>;
}

const CATEGORY_COLORS: Record<string, string> = {
  Billing: '#38bdf8',
  'Account/Login': '#a855f7',
  Delivery: '#f59e0b',
  Security: '#f43f5e',
  Technical: '#10b981',
  Other: '#64748b',
};

const FALLBACK_COLORS = ['#38bdf8', '#a855f7', '#f59e0b', '#f43f5e', '#10b981', '#64748b', '#ec4899'];

export const CategoryPieChart: React.FC<CategoryPieChartProps> = ({ data }) => {
  // Aggregate case-insensitively and filter out zeros
  const aggregated: Record<string, number> = {};
  for (const [rawKey, count] of Object.entries(data || {})) {
    if (count <= 0) continue;
    let key = rawKey.trim();
    if (key.toLowerCase() === 'billing') key = 'Billing';
    else if (key.toLowerCase() === 'account/login' || key.toLowerCase() === 'account') key = 'Account/Login';
    else if (key.toLowerCase() === 'delivery') key = 'Delivery';
    else if (key.toLowerCase() === 'security') key = 'Security';
    else if (key.toLowerCase() === 'technical') key = 'Technical';
    else if (key.toLowerCase() === 'unknown') key = 'Other';

    aggregated[key] = (aggregated[key] || 0) + count;
  }

  const chartData = Object.entries(aggregated).map(([name, value]) => ({
    name,
    value,
  }));

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-xs italic">
        No category distribution data recorded yet
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="45%"
            innerRadius={52}
            outerRadius={84}
            paddingAngle={4}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={CATEGORY_COLORS[entry.name] || FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
                stroke="#0f172a"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '12px',
            }}
          />
          <Legend
            verticalAlign="bottom"
            wrapperStyle={{ paddingTop: '14px', fontSize: '11px', color: '#94a3b8' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
