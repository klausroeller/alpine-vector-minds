'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  GraduationCap,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Search,
  Loader2,
  CheckCircle2,
  Info,
  XCircle,
  ExternalLink,
  X,
  Ticket,
} from 'lucide-react';
import Link from 'next/link';
import { AppLayout } from '@/components/layout/app-layout';
import { EventCard } from '@/components/learning/event-card';
import { ReviewDialog } from '@/components/learning/review-dialog';
import { ProvenanceChain } from '@/components/knowledge/provenance-chain';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  api,
  ApiError,
  type LearningEvent,
  type DetectGapResponse,
  type KBArticleDetail,
} from '@/lib/api';

const PAGE_SIZE = 15;
const STATUS_TABS = ['all', 'Pending', 'Approved', 'Rejected'] as const;
const ARTICLE_PREVIEW_LENGTH = 500;

export default function LearningPage() {
  const [events, setEvents] = useState<LearningEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Review dialog state
  const [reviewTarget, setReviewTarget] = useState<{
    id: string;
    action: 'Approved' | 'Rejected';
  } | null>(null);
  const [reviewing, setReviewing] = useState(false);

  // Detect Gap state
  const [gapOpen, setGapOpen] = useState(false);
  const [gapTicketId, setGapTicketId] = useState('');
  const [gapLoading, setGapLoading] = useState(false);
  const [gapResult, setGapResult] = useState<DetectGapResponse | null>(null);
  const [gapError, setGapError] = useState<string | null>(null);

  // Post-approval feedback state
  const [approvalFeedback, setApprovalFeedback] = useState<{
    type: 'approved' | 'rejected';
    article?: KBArticleDetail;
    articleId?: string;
  } | null>(null);

  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listLearningEvents({
        status: statusFilter !== 'all' ? statusFilter : undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setEvents(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  useEffect(() => {
    setPage(1);
  }, [statusFilter]);

  const handleDetectGap = async () => {
    if (!gapTicketId.trim() || gapLoading) return;
    setGapLoading(true);
    setGapResult(null);
    setGapError(null);
    try {
      const result = await api.detectGap(gapTicketId.trim());
      setGapResult(result);
      // Refresh event list if a gap was detected (new Pending event)
      if (result.gap_detected) {
        await fetchEvents();
      }
    } catch (err) {
      setGapError(
        err instanceof ApiError
          ? err.debugMessage
          : err instanceof Error
            ? err.message
            : 'Gap detection failed',
      );
    } finally {
      setGapLoading(false);
    }
  };

  const handleReviewConfirm = async () => {
    if (!reviewTarget) return;
    setReviewing(true);
    setApprovalFeedback(null);
    try {
      const result = await api.reviewLearningEvent(reviewTarget.id, reviewTarget.action);

      if (reviewTarget.action === 'Approved' && result.kb_article_status) {
        // Find the event to get the proposed article ID
        const event = events.find((e) => e.id === reviewTarget.id);
        const articleId = event?.proposed_kb_article_id;
        if (articleId) {
          try {
            const article = await api.getKBArticle(articleId);
            setApprovalFeedback({ type: 'approved', article, articleId });
          } catch {
            // If article fetch fails, still show basic approval message
            setApprovalFeedback({ type: 'approved', articleId });
          }
        } else {
          setApprovalFeedback({ type: 'approved' });
        }
      } else if (reviewTarget.action === 'Rejected') {
        setApprovalFeedback({ type: 'rejected' });
      }

      setReviewTarget(null);
      await fetchEvents();
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Review failed');
      setReviewTarget(null);
    } finally {
      setReviewing(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Learning Feed
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {total > 0 ? `${total.toLocaleString()} events` : 'Review knowledge gap detections'}
          </p>
        </div>

        {/* Detect Gap section */}
        <div className="mb-6 rounded-xl border border-white/[0.06] bg-[#0a1628]/60">
          <button
            onClick={() => setGapOpen(!gapOpen)}
            className="flex w-full items-center justify-between px-5 py-4 text-left"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-500/10 ring-1 ring-teal-500/20">
                <Search className="h-4 w-4 text-teal-400" />
              </div>
              <div>
                <span className="text-sm font-medium text-white">Detect Gap</span>
                <span className="ml-2 text-xs text-slate-500">Analyze a ticket for knowledge gaps</span>
              </div>
            </div>
            {gapOpen ? (
              <ChevronUp className="h-4 w-4 text-slate-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-slate-500" />
            )}
          </button>

          {gapOpen && (
            <div className="border-t border-white/[0.06] px-5 pb-5 pt-4">
              <div className="flex gap-3">
                <Input
                  placeholder="Enter ticket ID (e.g. CS-38908386)"
                  value={gapTicketId}
                  onChange={(e) => setGapTicketId(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleDetectGap();
                  }}
                  disabled={gapLoading}
                  className="border-white/[0.08] bg-white/[0.03] text-slate-200 placeholder:text-slate-600"
                />
                <Button
                  onClick={handleDetectGap}
                  disabled={!gapTicketId.trim() || gapLoading}
                  className="shrink-0 bg-gradient-to-r from-teal-600 to-cyan-600 text-white hover:from-teal-500 hover:to-cyan-500 disabled:opacity-40"
                >
                  {gapLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    'Detect Gap'
                  )}
                </Button>
              </div>

              {/* Gap detection error */}
              {gapError && (
                <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
                  {gapError}
                </div>
              )}

              {/* Gap detection result: gap found */}
              {gapResult?.gap_detected && gapResult.proposed_article && (
                <div className="mt-4 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span className="text-sm font-medium text-emerald-400">
                      Knowledge gap detected — draft article created
                    </span>
                  </div>
                  <div className="rounded-lg border border-white/[0.06] bg-[#0a1628]/80 p-4">
                    <h4 className="text-sm font-medium text-white">
                      {gapResult.proposed_article.title}
                    </h4>
                    <p className="mt-2 text-xs leading-relaxed text-slate-400">
                      {gapResult.proposed_article.body.length > ARTICLE_PREVIEW_LENGTH
                        ? gapResult.proposed_article.body.slice(0, ARTICLE_PREVIEW_LENGTH) + '...'
                        : gapResult.proposed_article.body}
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <Badge variant="outline" className="border-amber-500/30 text-amber-400">
                        <Ticket className="mr-1 h-3 w-3" />
                        Created from {gapTicketId.trim()}
                      </Badge>
                      <Badge variant="outline" className="border-slate-500/30 text-slate-400">
                        {gapResult.proposed_article.status}
                      </Badge>
                    </div>
                  </div>
                  {gapResult.detected_gap && (
                    <p className="mt-3 text-xs text-slate-500">
                      <span className="font-medium text-slate-400">Gap:</span>{' '}
                      {gapResult.detected_gap}
                    </p>
                  )}
                </div>
              )}

              {/* Gap detection result: no gap */}
              {gapResult && !gapResult.gap_detected && (
                <div className="mt-4 rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Info className="h-4 w-4 text-blue-400" />
                    <span className="text-sm font-medium text-blue-400">
                      No gap detected — existing KB already covers this scenario
                    </span>
                  </div>
                  {gapResult.detected_gap && (
                    <p className="text-xs text-slate-400">{gapResult.detected_gap}</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Post-approval / post-rejection feedback panel */}
        {approvalFeedback && (
          <div className="mb-6">
            {approvalFeedback.type === 'approved' ? (
              <div className="relative rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
                <button
                  onClick={() => setApprovalFeedback(null)}
                  className="absolute right-4 top-4 text-slate-500 hover:text-slate-300"
                >
                  <X className="h-4 w-4" />
                </button>
                <div className="mb-4 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  <span className="text-sm font-semibold text-emerald-400">
                    Article approved and now searchable
                  </span>
                </div>

                {approvalFeedback.article ? (
                  <>
                    <div className="rounded-lg border border-white/[0.06] bg-[#0a1628]/80 p-4">
                      <Link
                        href={`/knowledge/${approvalFeedback.article.id}`}
                        className="text-sm font-medium text-teal-400 hover:text-teal-300 hover:underline"
                      >
                        {approvalFeedback.article.title}
                      </Link>
                      <p className="mt-2 text-xs leading-relaxed text-slate-400">
                        {approvalFeedback.article.body.length > ARTICLE_PREVIEW_LENGTH
                          ? approvalFeedback.article.body.slice(0, ARTICLE_PREVIEW_LENGTH) + '...'
                          : approvalFeedback.article.body}
                      </p>
                    </div>

                    {/* Provenance chain */}
                    {approvalFeedback.article.lineage.length > 0 && (
                      <div className="mt-4">
                        <span className="mb-2 block text-xs font-medium text-slate-500">
                          Provenance
                        </span>
                        <ProvenanceChain lineage={approvalFeedback.article.lineage} />
                      </div>
                    )}

                    {/* Verify in Copilot button */}
                    <div className="mt-4">
                      <Link
                        href={`/copilot?q=${encodeURIComponent(approvalFeedback.article.title)}`}
                      >
                        <Button
                          size="sm"
                          className="bg-gradient-to-r from-teal-600 to-cyan-600 text-white hover:from-teal-500 hover:to-cyan-500"
                        >
                          <ExternalLink className="mr-2 h-3.5 w-3.5" />
                          Verify in Copilot
                        </Button>
                      </Link>
                    </div>
                  </>
                ) : (
                  <p className="text-xs text-slate-400">
                    The article has been activated and is now searchable in the knowledge base.
                  </p>
                )}
              </div>
            ) : (
              <div className="relative rounded-xl border border-slate-500/20 bg-slate-500/5 p-5">
                <button
                  onClick={() => setApprovalFeedback(null)}
                  className="absolute right-4 top-4 text-slate-500 hover:text-slate-300"
                >
                  <X className="h-4 w-4" />
                </button>
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-slate-400" />
                  <span className="text-sm font-medium text-slate-400">
                    Event rejected — article archived
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Status tabs */}
        <Tabs
          value={statusFilter}
          onValueChange={setStatusFilter}
          className="mb-6"
        >
          <TabsList className="bg-white/[0.03]">
            {STATUS_TABS.map((tab) => (
              <TabsTrigger key={tab} value={tab} className="text-sm">
                {tab === 'all' ? 'All' : tab}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {error && (
          <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Events list */}
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="rounded-xl border border-white/[0.06] border-l-2 border-l-slate-700 bg-[#0a1628]/60 p-5"
              >
                <Skeleton className="mb-3 h-5 w-20" />
                <Skeleton className="mb-2 h-4 w-40" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="mt-1 h-4 w-3/4" />
              </div>
            ))}
          </div>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.03] ring-1 ring-white/[0.06]">
              <GraduationCap className="h-6 w-6 text-slate-600" />
            </div>
            <p className="text-sm font-medium text-slate-400">No events found</p>
            <p className="mt-1 text-xs text-slate-600">
              Learning events will appear here as the system detects knowledge gaps
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {events.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  reviewing={reviewing}
                  onApprove={(id) =>
                    setReviewTarget({ id, action: 'Approved' })
                  }
                  onReject={(id) =>
                    setReviewTarget({ id, action: 'Rejected' })
                  }
                />
              ))}
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

      {/* Review confirmation dialog */}
      <ReviewDialog
        open={reviewTarget !== null}
        onOpenChange={(open) => {
          if (!open) setReviewTarget(null);
        }}
        action={reviewTarget?.action ?? null}
        onConfirm={handleReviewConfirm}
        loading={reviewing}
      />
    </AppLayout>
  );
}
