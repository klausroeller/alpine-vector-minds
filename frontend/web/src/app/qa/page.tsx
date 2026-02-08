'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  api,
  ApiError,
  type QAScoreListItem,
  type QAScoreResponse,
  type DashboardMetrics,
} from '@/lib/api';
import { cn } from '@/lib/utils';

const PAGE_SIZE = 15;

type FilterTab = 'all' | 'unscored' | 'scored';

const CATEGORY_LABELS: Record<string, string> = {
  greeting_empathy: 'Greeting & Empathy',
  issue_identification: 'Issue Identification',
  troubleshooting_quality: 'Troubleshooting Quality',
  resolution_accuracy: 'Resolution Accuracy',
  documentation_quality: 'Documentation Quality',
  compliance_safety: 'Compliance & Safety',
};

function scoreColor(score: number | null): string {
  if (score === null) return 'text-slate-500';
  if (score >= 80) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-400';
  return 'text-red-400';
}

function scoreBg(score: number | null): string {
  if (score === null) return 'bg-slate-500/10';
  if (score >= 80) return 'bg-emerald-500/10';
  if (score >= 50) return 'bg-amber-500/10';
  return 'bg-red-500/10';
}

function scoreBarColor(score: number): string {
  if (score >= 80) return '[&>div]:bg-emerald-500';
  if (score >= 50) return '[&>div]:bg-amber-500';
  return '[&>div]:bg-red-500';
}

export default function QAPage() {
  const [items, setItems] = useState<QAScoreListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<FilterTab>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Summary stats
  const [stats, setStats] = useState<DashboardMetrics['qa'] | null>(null);

  // Expanded detail
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<QAScoreResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Score action
  const [scoringId, setScoringId] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const scored = filter === 'all' ? undefined : filter === 'scored';
      const data = await api.listConversations({ scored, page, page_size: PAGE_SIZE });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setLoading(false);
    }
  }, [page, filter]);

  const fetchStats = useCallback(async () => {
    try {
      const metrics = await api.getDashboardMetrics();
      setStats(metrics.qa ?? null);
    } catch {
      // Non-critical
    }
  }, []);

  useEffect(() => {
    fetchConversations();
    fetchStats();
  }, [fetchConversations, fetchStats]);

  // Reset page when filter changes
  const handleFilterChange = (tab: FilterTab) => {
    setFilter(tab);
    setPage(1);
  };

  const handleScore = async (conversationId: string) => {
    setScoringId(conversationId);
    setError(null);
    try {
      await api.scoreConversation(conversationId);
      await fetchConversations();
      await fetchStats();
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Scoring failed');
    } finally {
      setScoringId(null);
    }
  };

  const handleExpand = async (conversationId: string) => {
    if (expandedId === conversationId) {
      setExpandedId(null);
      setDetail(null);
      return;
    }
    setExpandedId(conversationId);
    setDetail(null);
    setDetailLoading(true);
    try {
      const data = await api.getQADetail(conversationId);
      setDetail(data);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            QA Scores
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Conversation quality assessment against 6-category rubric
          </p>
        </div>

        {/* Summary stats */}
        {stats && (
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-white/[0.06] bg-[#0a1628]/80 p-4">
              <p className="text-2xl font-bold text-white">{stats.total_scored}</p>
              <p className="text-sm text-slate-500">Conversations Scored</p>
            </div>
            <div className="rounded-xl border border-white/[0.06] bg-[#0a1628]/80 p-4">
              <p className={cn('text-2xl font-bold', scoreColor(stats.average_score))}>
                {stats.average_score.toFixed(1)}
              </p>
              <p className="text-sm text-slate-500">Average Score</p>
            </div>
            <div className="rounded-xl border border-white/[0.06] bg-[#0a1628]/80 p-4">
              <p className={cn('text-2xl font-bold', stats.red_flag_count > 0 ? 'text-red-400' : 'text-emerald-400')}>
                {stats.red_flag_count}
              </p>
              <p className="text-sm text-slate-500">Red Flags</p>
            </div>
          </div>
        )}

        {/* Filter tabs */}
        <div className="mb-6 flex gap-1 rounded-lg bg-white/[0.03] p-1">
          {(['all', 'unscored', 'scored'] as FilterTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => handleFilterChange(tab)}
              className={cn(
                'flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                filter === tab
                  ? 'bg-white/[0.08] text-white'
                  : 'text-slate-500 hover:text-slate-300',
              )}
            >
              {tab === 'all' ? 'All' : tab === 'unscored' ? 'Unscored' : 'Scored'}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Conversations list */}
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-white/[0.06] bg-[#0a1628]/60 p-5">
                <Skeleton className="mb-3 h-5 w-20" />
                <Skeleton className="mb-2 h-4 w-40" />
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.03] ring-1 ring-white/[0.06]">
              <ShieldCheck className="h-6 w-6 text-slate-600" />
            </div>
            <p className="text-sm font-medium text-slate-400">
              {filter === 'scored' ? 'No scored conversations yet' : filter === 'unscored' ? 'All conversations have been scored' : 'No conversations found'}
            </p>
            <p className="mt-1 text-xs text-slate-600">
              {filter === 'scored' ? 'Score conversations from the "Unscored" tab' : ''}
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {items.map((item) => {
                const isScored = item.scored_at !== null;
                return (
                  <div
                    key={item.conversation_id}
                    className="rounded-xl border border-white/[0.06] bg-[#0a1628]/60 transition-all duration-200 hover:border-white/[0.1]"
                  >
                    <div className="flex items-center justify-between p-5">
                      <div className="flex items-center gap-4">
                        {/* Score badge or unscored indicator */}
                        <div className={cn('flex h-12 w-12 shrink-0 items-center justify-center rounded-xl', scoreBg(item.overall_score))}>
                          {isScored ? (
                            <span className={cn('text-lg font-bold', scoreColor(item.overall_score))}>
                              {item.overall_score !== null ? Math.round(item.overall_score) : '—'}
                            </span>
                          ) : (
                            <ShieldCheck className="h-5 w-5 text-slate-600" />
                          )}
                        </div>

                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm text-slate-300">
                              {item.conversation_id}
                            </span>
                            <span className="text-xs text-slate-600">
                              {item.ticket_id}
                            </span>
                          </div>
                          <div className="mt-1 flex items-center gap-2">
                            {item.agent_name && (
                              <span className="text-xs text-slate-500">{item.agent_name}</span>
                            )}
                            {item.channel && (
                              <Badge variant="outline" className="border-slate-500/20 text-xs text-slate-500">
                                {item.channel}
                              </Badge>
                            )}
                            {item.red_flags.length > 0 && item.red_flags.map((flag, i) => (
                              <Badge key={i} variant="outline" className="gap-1 border-red-500/30 text-xs text-red-400">
                                <AlertTriangle className="h-3 w-3" />
                                {flag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Action: Score button or expand toggle */}
                      {isScored ? (
                        <button onClick={() => handleExpand(item.conversation_id)}>
                          {expandedId === item.conversation_id ? (
                            <ChevronUp className="h-4 w-4 text-slate-500" />
                          ) : (
                            <ChevronDown className="h-4 w-4 text-slate-500" />
                          )}
                        </button>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleScore(item.conversation_id)}
                          disabled={scoringId === item.conversation_id}
                          className="bg-gradient-to-r from-teal-600 to-cyan-600 text-white hover:from-teal-500 hover:to-cyan-500 disabled:opacity-40"
                        >
                          {scoringId === item.conversation_id ? (
                            <>
                              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                              Scoring...
                            </>
                          ) : (
                            <>
                              <ShieldCheck className="mr-1.5 h-3.5 w-3.5" />
                              Score
                            </>
                          )}
                        </Button>
                      )}
                    </div>

                    {/* Expanded detail */}
                    {expandedId === item.conversation_id && isScored && (
                      <div className="border-t border-white/[0.06] px-5 pb-5 pt-4">
                        {detailLoading ? (
                          <div className="space-y-3">
                            {Array.from({ length: 6 }).map((_, i) => (
                              <Skeleton key={i} className="h-6 w-full" />
                            ))}
                          </div>
                        ) : detail ? (
                          <div className="space-y-4">
                            {/* Category breakdown */}
                            <div className="space-y-3">
                              {Object.entries(detail.categories).map(([key, cat]) => (
                                <div key={key}>
                                  <div className="mb-1 flex items-center justify-between">
                                    <span className="text-xs font-medium text-slate-300">
                                      {CATEGORY_LABELS[key] || key}
                                      <span className="ml-1 text-slate-600">
                                        ({Math.round(cat.weight * 100)}%)
                                      </span>
                                    </span>
                                    <span className={cn('text-xs font-bold', scoreColor(cat.score))}>
                                      {Math.round(cat.score)}
                                    </span>
                                  </div>
                                  <Progress
                                    value={cat.score}
                                    className={cn('h-2 bg-white/[0.04]', scoreBarColor(cat.score))}
                                  />
                                  <p className="mt-1 text-xs text-slate-500">{cat.feedback}</p>
                                </div>
                              ))}
                            </div>

                            {/* Summary */}
                            {detail.summary && (
                              <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                                <p className="text-xs text-slate-400">{detail.summary}</p>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500">Failed to load details</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="border-white/[0.06] text-slate-400"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-slate-500">
                  {page} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="border-white/[0.06] text-slate-400"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  );
}
