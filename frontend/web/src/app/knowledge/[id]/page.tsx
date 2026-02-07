'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, BookOpen } from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { ProvenanceChain } from '@/components/knowledge/provenance-chain';
import { api, type KBArticleDetail } from '@/lib/api';

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

export default function ArticleDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [article, setArticle] = useState<KBArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArticle = useCallback(async () => {
    try {
      const data = await api.getKBArticle(id);
      setArticle(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load article');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchArticle();
  }, [fetchArticle]);

  const source = SOURCE_BADGE[article?.source_type ?? ''];
  const status = STATUS_BADGE[article?.status ?? ''] ?? STATUS_BADGE.ACTIVE;

  return (
    <AppLayout>
      <div className="mx-auto max-w-3xl px-6 py-8">
        {/* Back link */}
        <Link
          href="/knowledge"
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-300"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Knowledge Base
        </Link>

        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <div className="flex gap-2">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-14" />
            </div>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 ring-1 ring-red-500/20">
              <BookOpen className="h-6 w-6 text-red-400" />
            </div>
            <p className="text-sm font-medium text-slate-400">{error}</p>
          </div>
        ) : article ? (
          <article>
            {/* Title + badges */}
            <h1 className="mb-3 text-2xl font-bold tracking-tight text-white">
              {article.title}
            </h1>
            <div className="mb-6 flex flex-wrap items-center gap-2">
              {source && (
                <Badge variant="outline" className={source.className}>
                  {source.label}
                </Badge>
              )}
              <Badge variant="outline" className={status.className}>
                {status.label}
              </Badge>
              {article.category && (
                <Badge
                  variant="outline"
                  className="border-slate-500/20 bg-slate-500/10 text-slate-400"
                >
                  {article.category}
                </Badge>
              )}
              {article.module && (
                <span className="text-xs text-slate-600">{article.module}</span>
              )}
            </div>

            {/* Body */}
            <div className="prose prose-invert max-w-none text-sm leading-relaxed text-slate-300">
              {article.body.split('\n').map((paragraph, i) => (
                <p key={i} className="mb-3">
                  {paragraph}
                </p>
              ))}
            </div>

            {/* Provenance */}
            {article.lineage.length > 0 && (
              <>
                <Separator className="my-8 bg-white/[0.06]" />
                <div>
                  <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-500">
                    Provenance
                  </h2>
                  <ProvenanceChain lineage={article.lineage} />
                </div>
              </>
            )}

            {/* Metadata footer */}
            <Separator className="my-8 bg-white/[0.06]" />
            <div className="flex flex-wrap gap-6 text-xs text-slate-600">
              <div>
                <span className="uppercase tracking-wider">Created</span>{' '}
                <span className="text-slate-500">
                  {new Date(article.created_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </span>
              </div>
              <div>
                <span className="uppercase tracking-wider">Updated</span>{' '}
                <span className="text-slate-500">
                  {new Date(article.updated_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </span>
              </div>
              {article.tags && (
                <div>
                  <span className="uppercase tracking-wider">Tags</span>{' '}
                  <span className="text-slate-500">{article.tags}</span>
                </div>
              )}
            </div>
          </article>
        ) : null}
      </div>
    </AppLayout>
  );
}
