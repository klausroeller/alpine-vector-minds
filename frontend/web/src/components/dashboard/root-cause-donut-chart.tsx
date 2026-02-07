'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { CategoryCount } from '@/lib/api';

interface RootCauseDonutChartProps {
  data: CategoryCount[];
  loading?: boolean;
}

const CAUSE_COLORS = [
  '#2dd4bf', '#818cf8', '#f472b6', '#fbbf24',
  '#34d399', '#60a5fa', '#c084fc', '#fb923c',
  '#a3e635', '#f87171',
];

export function RootCauseDonutChart({ data, loading }: RootCauseDonutChartProps) {
  const top8 = data.slice(0, 8);

  return (
    <Card className="border-white/[0.06] bg-[#0a1628]/80">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-400">
          Root Causes
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Skeleton className="h-44 w-44 rounded-full" />
          </div>
        ) : top8.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-600">No data yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={top8}
                cx="50%"
                cy="45%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={3}
                dataKey="count"
                nameKey="name"
                strokeWidth={0}
              >
                {top8.map((_, i) => (
                  <Cell
                    key={i}
                    fill={CAUSE_COLORS[i % CAUSE_COLORS.length]}
                    fillOpacity={0.85}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0c1a2a',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: '8px',
                  color: '#e2e8f0',
                  fontSize: 13,
                }}
              />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                iconSize={8}
                formatter={(value: string) => (
                  <span className="text-xs text-slate-400">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
