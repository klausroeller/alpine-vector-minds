'use client';

import { useCallback, useEffect, useState } from 'react';
import { BookOpen, GraduationCap, Ticket, ScrollText } from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { MetricCard } from '@/components/dashboard/metric-card';
import { CategoryBarChart } from '@/components/dashboard/category-bar-chart';
import { PriorityDonutChart } from '@/components/dashboard/priority-donut-chart';
import { RootCauseDonutChart } from '@/components/dashboard/root-cause-donut-chart';
import { api, ApiError, type DashboardMetrics } from '@/lib/api';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setError(null);
      const data = await api.getDashboardMetrics();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return (
    <AppLayout>
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-white">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">
            Platform overview and key metrics
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Metric cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            icon={BookOpen}
            label="KB Articles"
            value={metrics?.knowledge_base.total_articles ?? 0}
            gradient="bg-gradient-to-br from-teal-500/20 to-cyan-500/10"
            loading={loading}
          />
          <MetricCard
            icon={GraduationCap}
            label="Learning Events"
            value={metrics?.learning.total_events ?? 0}
            gradient="bg-gradient-to-br from-violet-500/20 to-purple-500/10"
            loading={loading}
          />
          <MetricCard
            icon={Ticket}
            label="Tickets"
            value={metrics?.tickets.total ?? 0}
            gradient="bg-gradient-to-br from-amber-500/20 to-orange-500/10"
            loading={loading}
          />
          <MetricCard
            icon={ScrollText}
            label="Scripts"
            value={metrics?.scripts.total ?? 0}
            gradient="bg-gradient-to-br from-rose-500/20 to-pink-500/10"
            loading={loading}
          />
        </div>

        {/* Charts row */}
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <CategoryBarChart
            data={metrics?.knowledge_base.categories ?? []}
            loading={loading}
          />
          <PriorityDonutChart
            data={metrics?.tickets.by_priority ?? {}}
            loading={loading}
          />
          <RootCauseDonutChart
            data={metrics?.tickets.by_root_cause ?? []}
            loading={loading}
          />
        </div>
      </div>
    </AppLayout>
  );
}
