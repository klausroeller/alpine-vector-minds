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
  PlayCircle,
  CheckCircle2,
  XCircle,
  MessageSquare,
  X,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  api,
  ApiError,
  type QAScoreListItem,
  type QADetailResponse,
  type DashboardMetrics,
} from '@/lib/api';
import { cn } from '@/lib/utils';

const PAGE_SIZE = 15;

type FilterTab = 'all' | 'unscored' | 'scored';

// --- Helpers ---

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

function paramLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function scoreBadge(score: string): { color: string; bg: string } {
  const s = score?.toLowerCase();
  if (s === 'yes') return { color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' };
  if (s === 'no') return { color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' };
  return { color: 'text-slate-500', bg: 'bg-slate-500/10 border-slate-500/20' };
}

// --- Transcript Parser ---

interface ChatMessage {
  speaker: string;
  text: string;
  isAgent: boolean;
}

function parseTranscript(transcript: string): ChatMessage[] {
  const messages: ChatMessage[] = [];
  const lines = transcript.split('\n').filter((l) => l.trim());

  for (const line of lines) {
    // Match patterns like "Agent: ...", "Caller: ...", "Name (Company): ...", "Name: ..."
    const match = line.match(/^([^:]+?):\s*(.+)$/);
    if (match) {
      const speaker = match[1].trim();
      const text = match[2].trim();
      const isAgent =
        speaker.toLowerCase() === 'agent' ||
        speaker.toLowerCase().includes('(exampleco)') ||
        speaker.toLowerCase().includes('support');
      messages.push({ speaker, text, isAgent });
    } else if (messages.length > 0) {
      // Continuation of previous message
      messages[messages.length - 1].text += '\n' + line.trim();
    }
  }
  return messages;
}

// --- QA Section Renderer ---

interface QAParam {
  score: string;
  tracking_items: string[];
  evidence: string;
}

function QASectionView({
  title,
  data,
  finalScore,
}: {
  title: string;
  data: Record<string, QAParam>;
  finalScore?: string;
}) {
  const [expanded, setExpanded] = useState(false);

  const entries = Object.entries(data).filter(
    ([key]) => key !== 'Final_Weighted_Score'
  );
  const yesCount = entries.filter(([, v]) => typeof v === 'object' && v.score?.toLowerCase() === 'yes').length;
  const noCount = entries.filter(([, v]) => typeof v === 'object' && v.score?.toLowerCase() === 'no').length;
  const total = entries.filter(([, v]) => typeof v === 'object' && v.score?.toLowerCase() !== 'n/a').length;

  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02]">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-3"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-200">{title}</span>
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-emerald-400">{yesCount} Yes</span>
            <span className="text-slate-600">/</span>
            <span className="text-red-400">{noCount} No</span>
            <span className="text-slate-600">/ {total} rated</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {finalScore && (
            <span className={cn('text-sm font-bold', scoreColor(parseFloat(finalScore) || null))}>
              {finalScore}
            </span>
          )}
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-slate-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-500" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/[0.04] px-3 pb-3 pt-2 space-y-2">
          {entries.map(([key, val]) => {
            if (typeof val !== 'object' || !val.score) return null;
            const badge = scoreBadge(val.score);
            return (
              <div key={key} className="rounded-md bg-white/[0.02] p-2.5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-300">
                    {paramLabel(key)}
                  </span>
                  <span className={cn('text-xs font-bold px-2 py-0.5 rounded border', badge.bg, badge.color)}>
                    {val.score}
                  </span>
                </div>
                {val.evidence && (
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{val.evidence}</p>
                )}
                {val.tracking_items && val.tracking_items.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {val.tracking_items.map((item, i) => (
                      <span
                        key={i}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// --- Transcript Viewer ---

function TranscriptViewer({
  transcript,
  onClose,
}: {
  transcript: string;
  onClose: () => void;
}) {
  const messages = parseTranscript(transcript);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-2xl max-h-[80vh] flex flex-col rounded-2xl border border-white/[0.08] bg-[#0a1628] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-teal-400" />
            <span className="text-sm font-medium text-white">Conversation Transcript</span>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-8">No messages to display</p>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  'flex',
                  msg.isAgent ? 'justify-start' : 'justify-end',
                )}
              >
                <div
                  className={cn(
                    'max-w-[80%] rounded-2xl px-4 py-2.5',
                    msg.isAgent
                      ? 'rounded-bl-md bg-slate-700/50 border border-slate-600/30'
                      : 'rounded-br-md bg-teal-600/20 border border-teal-500/20',
                  )}
                >
                  <p className={cn(
                    'text-[10px] font-medium mb-0.5',
                    msg.isAgent ? 'text-blue-400' : 'text-teal-400',
                  )}>
                    {msg.speaker}
                  </p>
                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {msg.text}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// --- Main Page ---

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
  const [detail, setDetail] = useState<QADetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Score actions
  const [scoringId, setScoringId] = useState<string | null>(null);
  const [scoringAll, setScoringAll] = useState(false);
  const [scoreAllProgress, setScoreAllProgress] = useState<string | null>(null);

  // Transcript modal
  const [transcriptContent, setTranscriptContent] = useState<string | null>(null);

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

  const handleScoreAll = async () => {
    setScoringAll(true);
    setError(null);
    setScoreAllProgress('Starting...');
    let totalScored = 0;
    let totalErrors = 0;

    try {
      // Score in batches of 50 until none remain
      let remaining = 1; // prime the loop
      while (remaining > 0) {
        const result = await api.scoreAll(50);
        totalScored += result.scored;
        totalErrors += result.errors;
        remaining = result.remaining;
        setScoreAllProgress(
          `Scored ${totalScored} conversations${totalErrors > 0 ? ` (${totalErrors} errors)` : ''}${remaining > 0 ? `, ${remaining} remaining...` : ''}`
        );
        // Refresh list after each batch
        await fetchConversations();
        await fetchStats();
        if (result.scored === 0 && result.errors === 0) break;
      }
      setScoreAllProgress(`Done! Scored ${totalScored} conversations${totalErrors > 0 ? ` with ${totalErrors} errors` : ''}.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Score All failed');
    } finally {
      setScoringAll(false);
      setTimeout(() => setScoreAllProgress(null), 5000);
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

  // Extract data from scores_json for detail view
  const scoresJson = detail?.scores_json as Record<string, unknown> | null;
  const interactionQA = scoresJson?.Interaction_QA as Record<string, QAParam> | undefined;
  const caseQA = scoresJson?.Case_QA as Record<string, QAParam> | undefined;
  const redFlagsData = scoresJson?.Red_Flags as Record<string, QAParam> | undefined;
  const evaluationMode = scoresJson?.Evaluation_Mode as string | undefined;
  const contactSummary = scoresJson?.Contact_Summary as string | undefined;
  const caseSummary = scoresJson?.Case_Summary as string | undefined;
  const qaRecommendation = scoresJson?.QA_Recommendation as string | undefined;
  const leaderAction = scoresJson?.Leader_Action_Required as string | undefined;

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              QA Scores
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Conversation quality assessment using the full QA evaluation rubric
            </p>
          </div>

          {/* Score All button */}
          <Button
            onClick={handleScoreAll}
            disabled={scoringAll}
            className="bg-gradient-to-r from-teal-600 to-cyan-600 text-white hover:from-teal-500 hover:to-cyan-500 disabled:opacity-40"
          >
            {scoringAll ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Scoring...
              </>
            ) : (
              <>
                <PlayCircle className="mr-2 h-4 w-4" />
                Score All
              </>
            )}
          </Button>
        </div>

        {/* Score All progress */}
        {scoreAllProgress && (
          <div className={cn(
            'mb-4 rounded-xl border p-3 text-sm',
            scoringAll
              ? 'border-teal-500/20 bg-teal-500/10 text-teal-400'
              : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400',
          )}>
            {scoringAll && <Loader2 className="mr-2 inline h-3.5 w-3.5 animate-spin" />}
            {scoreAllProgress}
          </div>
        )}

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
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {items.map((item) => {
                const isScored = item.scored_at !== null;
                const isExpanded = expandedId === item.conversation_id;
                return (
                  <div
                    key={item.conversation_id}
                    className="rounded-xl border border-white/[0.06] bg-[#0a1628]/60 transition-all duration-200 hover:border-white/[0.1]"
                  >
                    <div className="flex items-center justify-between p-5">
                      <div className="flex items-center gap-4">
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

                      {isScored ? (
                        <button onClick={() => handleExpand(item.conversation_id)}>
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4 text-slate-500" />
                          ) : (
                            <ChevronDown className="h-4 w-4 text-slate-500" />
                          )}
                        </button>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleScore(item.conversation_id)}
                          disabled={scoringId === item.conversation_id || scoringAll}
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
                    {isExpanded && isScored && (
                      <div className="border-t border-white/[0.06] px-5 pb-5 pt-4">
                        {detailLoading ? (
                          <div className="space-y-3">
                            {Array.from({ length: 4 }).map((_, i) => (
                              <Skeleton key={i} className="h-12 w-full" />
                            ))}
                          </div>
                        ) : detail ? (
                          <div className="space-y-4">
                            {/* Header: Mode + Recommendation + Transcript button */}
                            <div className="flex items-center gap-2 flex-wrap">
                              {evaluationMode && (
                                <Badge variant="outline" className="border-teal-500/20 text-teal-400 text-xs">
                                  {evaluationMode}
                                </Badge>
                              )}
                              {qaRecommendation && (
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    'text-xs',
                                    qaRecommendation.toLowerCase().includes('keep')
                                      ? 'border-emerald-500/20 text-emerald-400'
                                      : qaRecommendation.toLowerCase().includes('coaching')
                                        ? 'border-amber-500/20 text-amber-400'
                                        : 'border-red-500/20 text-red-400',
                                  )}
                                >
                                  {qaRecommendation}
                                </Badge>
                              )}
                              {leaderAction?.toLowerCase() === 'yes' && (
                                <Badge variant="outline" className="gap-1 border-red-500/30 text-red-400 text-xs">
                                  <AlertTriangle className="h-3 w-3" />
                                  Leader Action Required
                                </Badge>
                              )}
                              <div className="flex-1" />
                              {detail.transcript && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setTranscriptContent(detail.transcript)}
                                  className="border-white/[0.08] text-slate-400 hover:text-white text-xs"
                                >
                                  <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
                                  Show Transcript
                                </Button>
                              )}
                            </div>

                            {/* Interaction QA */}
                            {interactionQA && Object.keys(interactionQA).length > 0 && (
                              <QASectionView
                                title="Interaction QA (Call/Chat)"
                                data={interactionQA}
                                finalScore={interactionQA.Final_Weighted_Score as unknown as string}
                              />
                            )}

                            {/* Case QA */}
                            {caseQA && Object.keys(caseQA).length > 0 && (
                              <QASectionView
                                title="Case QA (Ticket)"
                                data={caseQA}
                                finalScore={caseQA.Final_Weighted_Score as unknown as string}
                              />
                            )}

                            {/* Red Flags */}
                            {redFlagsData && Object.keys(redFlagsData).length > 0 && (
                              <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                                <p className="text-sm font-medium text-slate-200 mb-2">Red Flags</p>
                                <div className="space-y-1.5">
                                  {Object.entries(redFlagsData).map(([key, val]) => {
                                    if (typeof val !== 'object' || !val.score) return null;
                                    const isYes = val.score.toLowerCase() === 'yes';
                                    return (
                                      <div key={key} className="flex items-center gap-2">
                                        {isYes ? (
                                          <XCircle className="h-3.5 w-3.5 text-red-400 shrink-0" />
                                        ) : (
                                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                                        )}
                                        <span className={cn('text-xs', isYes ? 'text-red-400' : 'text-slate-400')}>
                                          {paramLabel(key)}
                                        </span>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}

                            {/* Summaries */}
                            {(contactSummary || caseSummary) && (
                              <div className="space-y-2">
                                {contactSummary && (
                                  <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                                    <p className="text-xs font-medium text-slate-400 mb-1">Contact Summary</p>
                                    <p className="text-xs text-slate-300 leading-relaxed">{contactSummary}</p>
                                  </div>
                                )}
                                {caseSummary && (
                                  <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                                    <p className="text-xs font-medium text-slate-400 mb-1">Case Summary</p>
                                    <p className="text-xs text-slate-300 leading-relaxed">{caseSummary}</p>
                                  </div>
                                )}
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

      {/* Transcript modal */}
      {transcriptContent && (
        <TranscriptViewer
          transcript={transcriptContent}
          onClose={() => setTranscriptContent(null)}
        />
      )}
    </AppLayout>
  );
}
