'use client';

import { useCallback, useEffect, useState } from 'react';
import { GraduationCap, ChevronLeft, ChevronRight } from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { EventCard } from '@/components/learning/event-card';
import { ReviewDialog } from '@/components/learning/review-dialog';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { api, type LearningEvent } from '@/lib/api';

const PAGE_SIZE = 15;
const STATUS_TABS = ['all', 'Pending', 'Approved', 'Rejected'] as const;

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

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listLearningEvents({
        status: statusFilter !== 'all' ? statusFilter : undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setEvents(data.items);
      setTotal(data.total);
    } catch {
      // API not ready
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

  const handleReviewConfirm = async () => {
    if (!reviewTarget) return;
    setReviewing(true);
    try {
      await api.reviewLearningEvent(reviewTarget.id, reviewTarget.action);
      setReviewTarget(null);
      await fetchEvents();
    } catch {
      // Error handling
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
