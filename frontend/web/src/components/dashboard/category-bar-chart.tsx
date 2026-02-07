'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { CategoryCount } from '@/lib/api';

interface CategoryBarChartProps {
  data: CategoryCount[];
  loading?: boolean;
}

const BAR_COLORS = [
  '#2dd4bf', '#22d3ee', '#38bdf8', '#818cf8',
  '#a78bfa', '#c084fc', '#e879f9', '#f472b6',
  '#fb7185', '#fbbf24',
];

export function CategoryBarChart({ data, loading }: CategoryBarChartProps) {
  const top10 = data.slice(0, 10);

  return (
    <Card className="border-white/[0.06] bg-[#0a1628]/80">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-400">
          Top Categories
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-5 w-full" />
            ))}
          </div>
        ) : top10.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-600">No data yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={top10} layout="vertical" margin={{ left: 0, right: 12 }}>
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0c1a2a',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: '8px',
                  color: '#e2e8f0',
                  fontSize: 13,
                }}
                cursor={{ fill: 'rgba(255,255,255,0.02)' }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={24}>
                {top10.map((_, i) => (
                  <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
