'use client';

import { useCallback, useEffect, useState } from 'react';
import { BookOpen, GraduationCap, Ticket, ScrollText, ShieldCheck, Target, AlertTriangle, ThumbsUp, MessageSquare } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
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

            {/* QA Score Timeline */}
            {metrics.qa.monthly_scores && metrics.qa.monthly_scores.length > 0 && (
              <div className="mt-4 rounded-xl border border-white/[0.06] bg-[#0a1628]/80 p-6">
                <h3 className="mb-4 text-sm font-semibold text-slate-300">Avg. QA Score Over Time</h3>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={metrics.qa.monthly_scores.map((d) => ({
                        month: d.month,
                        score: d.avg_score,
                        count: d.count,
                      }))}
                      margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                    >
                      <defs>
                        <linearGradient id="qaScoreGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis
                        dataKey="month"
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        tickLine={false}
                        axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                        width={35}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f1d32',
                          border: '1px solid rgba(255,255,255,0.08)',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                        labelStyle={{ color: '#94a3b8' }}
                        itemStyle={{ color: '#14b8a6' }}
                        formatter={(value, _name, props) => {
                          const v = typeof value === 'number' ? value : 0;
                          const count = (props?.payload as { count?: number })?.count ?? 0;
                          return [`${v.toFixed(1)}% (${count} conversations)`, 'Avg Score'];
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="score"
                        stroke="#14b8a6"
                        strokeWidth={2}
                        fill="url(#qaScoreGradient)"
                        dot={{ r: 4, fill: '#14b8a6', strokeWidth: 0 }}
                        activeDot={{ r: 6, fill: '#14b8a6', stroke: '#0f1d32', strokeWidth: 2 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
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

              {/* Accuracy by Difficulty */}
              {metrics.evaluation.by_difficulty && Object.keys(metrics.evaluation.by_difficulty).length > 0 && (
                <div className="mt-6 border-t border-white/[0.06] pt-6">
                  <h3 className="mb-4 text-sm font-semibold text-slate-300">Accuracy by Difficulty</h3>
                  <div className="grid gap-4 sm:grid-cols-3">
                    {(['Easy', 'Medium', 'Hard'] as const).map((level) => {
                      const data = metrics.evaluation!.by_difficulty?.[level];
                      if (!data) return null;
                      const gradients: Record<string, string> = {
                        Easy: 'from-emerald-500/20 to-green-500/10',
                        Medium: 'from-amber-500/20 to-yellow-500/10',
                        Hard: 'from-red-500/20 to-rose-500/10',
                      };
                      const barColors: Record<string, string> = {
                        Easy: '[&>div]:from-emerald-500 [&>div]:to-green-400',
                        Medium: '[&>div]:from-amber-500 [&>div]:to-yellow-400',
                        Hard: '[&>div]:from-red-500 [&>div]:to-rose-400',
                      };
                      return (
                        <div
                          key={level}
                          className={`rounded-lg border border-white/[0.06] bg-gradient-to-br ${gradients[level]} p-4`}
                        >
                          <div className="mb-3 flex items-center justify-between">
                            <span className="text-sm font-semibold text-white">{level}</span>
                            <span className="text-xs text-slate-400">{data.count} questions</span>
                          </div>
                          <div className="space-y-3">
                            {[
                              { label: 'Classification', value: data.classification_correct },
                              { label: 'Hit@1', value: data.hit_at_1 },
                              { label: 'Hit@5', value: data.hit_at_5 },
                            ].map(({ label, value }) => (
                              <div key={label}>
                                <div className="mb-1 flex items-center justify-between">
                                  <span className="text-xs text-slate-400">{label}</span>
                                  <span className="text-xs font-bold text-white">
                                    {(value * 100).toFixed(1)}%
                                  </span>
                                </div>
                                <Progress
                                  value={value * 100}
                                  className={`h-1.5 bg-white/[0.06] [&>div]:bg-gradient-to-r ${barColors[level]}`}
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
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
