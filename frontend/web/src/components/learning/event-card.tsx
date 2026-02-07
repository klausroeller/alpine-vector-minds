'use client';

import Link from 'next/link';
import { Ticket, Lightbulb, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { LearningEvent } from '@/lib/api';

interface EventCardProps {
  event: LearningEvent;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  reviewing?: boolean;
}

const STATUS_CONFIG: Record<string, {
  label: string;
  className: string;
  border: string;
  icon: React.ElementType;
}> = {
  Pending: {
    label: 'Pending',
    className: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    border: 'border-l-amber-500/50',
    icon: Clock,
  },
  Approved: {
    label: 'Approved',
    className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    border: 'border-l-emerald-500/50',
    icon: CheckCircle2,
  },
  Rejected: {
    label: 'Rejected',
    className: 'bg-red-500/10 text-red-400 border-red-500/20',
    border: 'border-l-red-500/50',
    icon: XCircle,
  },
};

export function EventCard({ event, onApprove, onReject, reviewing }: EventCardProps) {
  const statusKey = event.final_status ?? 'Pending';
  const config = STATUS_CONFIG[statusKey] ?? STATUS_CONFIG.Pending;
  const isPending = statusKey === 'Pending';

  return (
    <div
      className={cn(
        'rounded-xl border border-white/[0.06] border-l-2 bg-[#0a1628]/60 p-5 transition-all duration-200',
        config.border
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          {/* Status badge */}
          <div className="mb-3">
            <Badge variant="outline" className={config.className}>
              <config.icon className="mr-1 h-3 w-3" />
              {config.label}
            </Badge>
          </div>

          {/* Trigger ticket */}
          {event.trigger_ticket_id && (
            <div className="mb-2 flex items-center gap-2 text-sm text-slate-400">
              <Ticket className="h-3.5 w-3.5 text-slate-600" />
              <span className="font-mono text-xs">{event.trigger_ticket_id.slice(0, 12)}</span>
            </div>
          )}

          {/* Detected gap */}
          {event.detected_gap && (
            <div className="mb-3 flex items-start gap-2">
              <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500/60" />
              <p className="text-sm leading-relaxed text-slate-300">
                {event.detected_gap}
              </p>
            </div>
          )}

          {/* Proposed article */}
          {event.proposed_kb_article_id && (
            <Link
              href={`/knowledge/${event.proposed_kb_article_id}`}
              className="inline-flex items-center gap-1.5 text-xs text-teal-400/80 transition-colors hover:text-teal-400"
            >
              View proposed article
              {event.proposed_kb_title && (
                <span className="text-slate-500">
                  — {event.proposed_kb_title}
                </span>
              )}
            </Link>
          )}

          <p className="mt-3 text-xs text-slate-600">
            {new Date(event.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>

        {/* Review actions */}
        {isPending && (
          <div className="flex shrink-0 gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={reviewing}
              onClick={() => onApprove(event.id)}
              className="border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300"
            >
              <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
              Approve
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={reviewing}
              onClick={() => onReject(event.id)}
              className="border-red-500/20 text-red-400 hover:bg-red-500/10 hover:text-red-300"
            >
              <XCircle className="mr-1 h-3.5 w-3.5" />
              Reject
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
