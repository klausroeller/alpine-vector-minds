'use client';

import { useCallback, useEffect, useState } from 'react';
import { BookOpen, GraduationCap, Ticket, ScrollText, ShieldCheck, Target, AlertTriangle, ThumbsUp, MessageSquare } from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { MetricCard } from '@/components/dashboard/metric-card';
import { CategoryBarChart } from '@/components/dashboard/category-bar-chart';
import { PriorityDonutChart } from '@/components/dashboard/priority-donut-chart';
import { RootCauseDonutChart } from '@/components/dashboard/root-cause-donut-chart';
import { Progress } from '@/components/ui/progress';
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

        {/* QA Metrics row */}
        {metrics?.qa && (
          <>
            <h2 className="mt-8 mb-4 text-lg font-semibold text-white">QA Quality</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              <MetricCard
                icon={ShieldCheck}
                label="QA Scored"
                value={metrics.qa.total_scored}
                gradient="bg-gradient-to-br from-blue-500/20 to-indigo-500/10"
                loading={loading}
              />
              <MetricCard
                icon={Target}
                label="Avg Score"
                value={metrics.qa.average_score.toFixed(1)}
                gradient="bg-gradient-to-br from-emerald-500/20 to-green-500/10"
                loading={loading}
              />
              <MetricCard
                icon={AlertTriangle}
                label="Red Flags"
                value={metrics.qa.red_flag_count}
                gradient="bg-gradient-to-br from-red-500/20 to-rose-500/10"
                loading={loading}
              />
            </div>
          </>
        )}

        {/* System Accuracy section */}
        {metrics?.evaluation && (
          <>
            <h2 className="mt-8 mb-4 text-lg font-semibold text-white">System Accuracy</h2>
            <div className="rounded-xl border border-white/[0.06] bg-[#0a1628]/80 p-6">
              <p className="mb-4 text-xs text-slate-500">
                {metrics.evaluation.total_questions} questions evaluated on{' '}
                {new Date(metrics.evaluation.evaluated_at).toLocaleDateString()}
              </p>
              <div className="space-y-4">
                {[
                  { label: 'Classification Accuracy', value: metrics.evaluation.classification_accuracy },
                  { label: 'Hit@1', value: metrics.evaluation.hit_at_1 },
                  { label: 'Hit@5', value: metrics.evaluation.hit_at_5 },
                  { label: 'Hit@10', value: metrics.evaluation.hit_at_10 },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-sm text-slate-300">{label}</span>
                      <span className="text-sm font-bold text-teal-400">
                        {(value * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress
                      value={value * 100}
                      className="h-2 bg-white/[0.04] [&>div]:bg-gradient-to-r [&>div]:from-teal-500 [&>div]:to-cyan-400"
                    />
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Feedback Metrics */}
        {metrics?.feedback && (
          <>
            <h2 className="mt-8 mb-4 text-lg font-semibold text-white">Copilot Feedback</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              <MetricCard
                icon={MessageSquare}
                label="Total Feedback"
                value={metrics.feedback.total_feedback}
                gradient="bg-gradient-to-br from-sky-500/20 to-blue-500/10"
                loading={loading}
              />
              <MetricCard
                icon={ThumbsUp}
                label="Helpful"
                value={metrics.feedback.helpful_count}
                gradient="bg-gradient-to-br from-emerald-500/20 to-green-500/10"
                loading={loading}
              />
              <MetricCard
                icon={Target}
                label="Helpful Rate"
                value={`${(metrics.feedback.helpful_rate * 100).toFixed(0)}%`}
                gradient="bg-gradient-to-br from-violet-500/20 to-purple-500/10"
                loading={loading}
              />
            </div>
          </>
        )}

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
