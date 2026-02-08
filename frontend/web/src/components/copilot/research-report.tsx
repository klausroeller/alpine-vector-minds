'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ChevronDown,
  ChevronUp,
  ScrollText,
  BookOpen,
  Ticket,
  FlaskConical,
  ExternalLink,
  Search,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { CopilotResearchResponse, EvidenceItem, RelatedResource, SubQueryInfo } from '@/lib/api';

interface ResearchReportViewProps {
  response: CopilotResearchResponse;
  visible: boolean;
}

const SOURCE_CONFIG: Record<string, {
  label: string;
  icon: React.ElementType;
  className: string;
}> = {
  kb_article: {
    label: 'KB Article',
    icon: BookOpen,
    className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  },
  script: {
    label: 'Script',
    icon: ScrollText,
    className: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  },
  ticket: {
    label: 'Ticket',
    icon: Ticket,
    className: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
};

function EvidenceCard({ item, index, visible }: { item: EvidenceItem; index: number; visible: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const source = SOURCE_CONFIG[item.source_type] ?? SOURCE_CONFIG.kb_article;
  const Icon = source.icon;

  return (
    <div
      className={cn(
        'transform transition-all duration-500 ease-out',
        visible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
      )}
      style={{ transitionDelay: visible ? `${(index + 1) * 100}ms` : '0ms' }}
    >
      <div className="group rounded-xl border border-white/[0.06] bg-[#0a1628]/60 p-4 transition-all duration-200 hover:border-white/[0.1] hover:bg-[#0a1628]/90">
        <div className="flex items-start gap-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-violet-500/10 text-xs font-bold text-violet-400 ring-1 ring-violet-500/20">
            {index + 1}
          </div>
          <div className="min-w-0 flex-1">
            <div className="mb-1.5 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className={cn('gap-1', source.className)}>
                <Icon className="h-3 w-3" />
                {source.label}
              </Badge>
              <Link
                href={`/knowledge/${item.source_id}`}
                className="font-mono text-[11px] text-violet-400/70 underline decoration-violet-400/30 transition-colors hover:text-violet-300 hover:decoration-violet-300"
              >
                {item.source_id}
              </Link>
            </div>

            <Link
              href={`/knowledge/${item.source_id}`}
              className="text-[14px] font-medium text-violet-300 underline decoration-violet-400/30 transition-colors hover:text-violet-200 hover:decoration-violet-300"
            >
              {item.title}
            </Link>

            <p className="mt-1.5 text-xs text-slate-400">{item.relevance}</p>

            {item.content_preview && (
              <div className="mt-2">
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-xs text-slate-500 transition-colors hover:text-slate-300"
                >
                  {expanded ? (
                    <><ChevronUp className="h-3 w-3" /> Hide preview</>
                  ) : (
                    <><ChevronDown className="h-3 w-3" /> Show preview</>
                  )}
                </button>
                {expanded && (
                  <p className="mt-2 text-sm leading-relaxed text-slate-400">
                    {item.content_preview}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function RelatedResourceItem({ item }: { item: RelatedResource }) {
  const source = SOURCE_CONFIG[item.source_type] ?? SOURCE_CONFIG.kb_article;
  const Icon = source.icon;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/[0.04] bg-white/[0.02] px-3 py-2">
      <Icon className="h-3.5 w-3.5 shrink-0 text-slate-500" />
      <div className="min-w-0 flex-1">
        <Link
          href={`/knowledge/${item.source_id}`}
          className="text-xs font-medium text-slate-300 underline decoration-slate-500/30 transition-colors hover:text-slate-200"
        >
          {item.title}
        </Link>
        <p className="mt-0.5 text-[11px] text-slate-600">{item.why_relevant}</p>
      </div>
      <Link href={`/knowledge/${item.source_id}`}>
        <ExternalLink className="h-3 w-3 text-slate-600 transition-colors hover:text-slate-400" />
      </Link>
    </div>
  );
}

function SubQueriesPanel({ subQueries }: { subQueries: SubQueryInfo[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border border-white/[0.04] bg-white/[0.02]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-3 text-xs text-slate-500 transition-colors hover:text-slate-400"
      >
        <Search className="h-3.5 w-3.5" />
        <span className="font-medium">Query Decomposition</span>
        <span className="ml-auto text-[11px] text-slate-600">{subQueries.length} sub-queries</span>
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>
      {open && (
        <div className="space-y-2 border-t border-white/[0.04] px-4 py-3">
          {subQueries.map((sq, i) => (
            <div key={i} className="flex items-start gap-2">
              <Badge variant="outline" className="shrink-0 border-slate-500/20 bg-slate-500/10 text-[10px] text-slate-400">
                {sq.pool}
              </Badge>
              <div>
                <p className="text-xs text-slate-300">{sq.query}</p>
                {sq.aspect && (
                  <p className="mt-0.5 text-[11px] text-slate-600">{sq.aspect}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function ResearchReportView({ response, visible }: ResearchReportViewProps) {
  const [relatedOpen, setRelatedOpen] = useState(false);
  const report = response.report;

  if (!report) return null;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div
        className={cn(
          'transform transition-all duration-500',
          visible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'
        )}
      >
        <div className="rounded-xl border-l-2 border-violet-500/40 bg-[#0a1628]/60 p-5">
          <div className="mb-3 flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-violet-400" />
            <span className="text-sm font-medium text-violet-400">Research Summary</span>
          </div>
          <div className="text-sm leading-relaxed text-slate-300 whitespace-pre-line">
            {report.summary}
          </div>
        </div>
      </div>

      {/* Evidence */}
      {report.evidence.length > 0 && (
        <div>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Evidence ({report.evidence.length})
          </h3>
          <div className="space-y-3">
            {report.evidence.map((item, i) => (
              <EvidenceCard key={item.source_id} item={item} index={i} visible={visible} />
            ))}
          </div>
        </div>
      )}

      {/* Related resources */}
      {report.related_resources.length > 0 && (
        <div className="rounded-xl border border-white/[0.04] bg-white/[0.02]">
          <button
            onClick={() => setRelatedOpen(!relatedOpen)}
            className="flex w-full items-center gap-2 px-4 py-3 text-xs text-slate-500 transition-colors hover:text-slate-400"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span className="font-medium">Related Resources</span>
            <span className="ml-auto text-[11px] text-slate-600">{report.related_resources.length}</span>
            {relatedOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
          {relatedOpen && (
            <div className="space-y-1.5 border-t border-white/[0.04] px-4 py-3">
              {report.related_resources.map((item) => (
                <RelatedResourceItem key={item.source_id} item={item} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sub-queries debug panel */}
      {response.sub_queries && response.sub_queries.length > 0 && (
        <SubQueriesPanel subQueries={response.sub_queries} />
      )}
    </div>
  );
}
