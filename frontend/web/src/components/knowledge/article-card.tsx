'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import type { KBArticleListItem } from '@/lib/api';

interface ArticleCardProps {
  article: KBArticleListItem;
}

const SOURCE_BADGE: Record<string, { label: string; className: string }> = {
  seed: {
    label: 'Seed',
    className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  },
  synthetic: {
    label: 'Synthetic',
    className: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  },
};

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  ACTIVE: {
    label: 'Active',
    className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  },
  DRAFT: {
    label: 'Draft',
    className: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
  ARCHIVED: {
    label: 'Archived',
    className: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  },
};

export function ArticleCard({ article }: ArticleCardProps) {
  const source = SOURCE_BADGE[article.source_type ?? ''];
  const status = STATUS_BADGE[article.status] ?? STATUS_BADGE.ACTIVE;

  return (
    <Link
      href={`/knowledge/${article.id}`}
      className="group block rounded-xl border border-white/[0.06] bg-[#0a1628]/60 p-5 transition-all duration-200 hover:border-white/[0.1] hover:bg-[#0a1628]/90"
    >
      <div className="mb-2 flex items-center gap-2">
        {source && (
          <Badge variant="outline" className={source.className}>
            {source.label}
          </Badge>
        )}
        <Badge variant="outline" className={status.className}>
          {status.label}
        </Badge>
        <span className="font-mono text-[11px] text-slate-500">{article.id}</span>
        {article.category && (
          <span className="text-xs text-slate-600">{article.category}</span>
        )}
      </div>

      <h3 className="mb-1.5 text-[15px] font-medium text-white transition-colors group-hover:text-teal-400">
        {article.title}
      </h3>

      <p className="line-clamp-2 text-sm leading-relaxed text-slate-500">
        {article.body_preview}
      </p>

      <p className="mt-3 text-xs text-slate-600">
        {new Date(article.created_at).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </p>
    </Link>
  );
}
