'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ChevronDown, ChevronUp, ScrollText, BookOpen, Ticket } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ProvenanceChain } from '@/components/knowledge/provenance-chain';
import { cn } from '@/lib/utils';
import type { SearchResult } from '@/lib/api';

interface ResultCardProps {
  result: SearchResult;
  index: number;
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

export function ResultCard({ result, index, visible }: ResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const source = SOURCE_CONFIG[result.source_type] ?? SOURCE_CONFIG.kb_article;
  const Icon = source.icon;
  const similarityPct = Math.round(result.similarity_score * 100);

  return (
    <div
      className={cn(
        'transform transition-all duration-500 ease-out',
        visible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
      )}
      style={{ transitionDelay: visible ? `${index * 100}ms` : '0ms' }}
    >
      <div className="group rounded-xl border border-white/[0.06] bg-[#0a1628]/60 p-5 transition-all duration-200 hover:border-white/[0.1] hover:bg-[#0a1628]/90">
        <div className="flex items-start gap-4">
          {/* Rank */}
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-sm font-bold text-slate-500 ring-1 ring-white/[0.06]">
            {result.rank}
          </div>

          <div className="min-w-0 flex-1">
            {/* Title + source badge */}
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className={cn('gap-1', source.className)}>
                <Icon className="h-3 w-3" />
                {source.label}
              </Badge>
              {result.category && (
                <span className="text-xs text-slate-600">{result.category}</span>
              )}
            </div>

            {result.source_type === 'kb_article' ? (
              <Link
                href={`/knowledge/${result.source_id}`}
                className="text-[15px] font-medium text-white transition-colors hover:text-teal-400"
              >
                {result.title}
              </Link>
            ) : (
              <p className="text-[15px] font-medium text-white">{result.title}</p>
            )}

            {/* Similarity bar */}
            <div className="mt-3 flex items-center gap-3">
              <div className="flex-1">
                <Progress
                  value={visible ? similarityPct : 0}
                  className="h-1.5 bg-white/[0.04] [&>div]:bg-gradient-to-r [&>div]:from-teal-500 [&>div]:to-cyan-400 [&>div]:transition-all [&>div]:duration-700"
                />
              </div>
              <span className="shrink-0 text-xs font-medium text-teal-400">
                {similarityPct}%
              </span>
            </div>

            {/* Expandable preview */}
            {result.content_preview && (
              <div className="mt-3">
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-xs text-slate-500 transition-colors hover:text-slate-300"
                >
                  {expanded ? (
                    <>
                      <ChevronUp className="h-3 w-3" /> Hide preview
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-3 w-3" /> Show preview
                    </>
                  )}
                </button>
                {expanded && (
                  <p className="mt-2 text-sm leading-relaxed text-slate-400">
                    {result.content_preview}
                  </p>
                )}
              </div>
            )}

            {/* Provenance (for KB) */}
            {result.provenance && expanded && (
              <div className="mt-3">
                <ProvenanceChain provenance={result.provenance} />
              </div>
            )}

            {/* Placeholders (for scripts) */}
            {result.placeholders && result.placeholders.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {result.placeholders.map((ph) => (
                  <Badge
                    key={ph}
                    variant="outline"
                    className="border-slate-500/20 bg-slate-500/10 text-xs text-slate-400"
                  >
                    {ph}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
