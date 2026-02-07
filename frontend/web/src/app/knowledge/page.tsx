'use client';

import { useCallback, useEffect, useState } from 'react';
import { BookOpen, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { ArticleFilters } from '@/components/knowledge/article-filters';
import { ArticleCard } from '@/components/knowledge/article-card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useDebounce } from '@/hooks/use-debounce';
import { api, ApiError, type KBArticleListItem } from '@/lib/api';

const PAGE_SIZE = 12;

export default function KnowledgePage() {
  const [articles, setArticles] = useState<KBArticleListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [sourceType, setSourceType] = useState('all');
  const [category, setCategory] = useState('all');
  const [status, setStatus] = useState('all');
  const [categories, setCategories] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const debouncedSearch = useDebounce(search, 300);

  const fetchArticles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listKBArticles({
        search: debouncedSearch || undefined,
        source_type: sourceType !== 'all' ? sourceType : undefined,
        category: category !== 'all' ? category : undefined,
        status: status !== 'all' ? status : undefined,
        page,
        page_size: PAGE_SIZE,
      });
      setArticles(data.items);
      setTotal(data.total);

      // Extract unique categories from results for filter
      const cats = new Set<string>();
      data.items.forEach((a) => {
        if (a.category) cats.add(a.category);
      });
      setCategories((prev) => {
        const merged = new Set([...prev, ...cats]);
        return Array.from(merged).sort();
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Failed to load articles');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, sourceType, category, status, page]);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  // Reset to page 1 on filter change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, sourceType, category, status]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const filtersContent = (
    <ArticleFilters
      search={search}
      onSearchChange={setSearch}
      sourceType={sourceType}
      onSourceTypeChange={setSourceType}
      category={category}
      onCategoryChange={setCategory}
      status={status}
      onStatusChange={setStatus}
      categories={categories}
    />
  );

  return (
    <AppLayout>
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Knowledge Base
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {total > 0 ? `${total.toLocaleString()} articles` : 'Browse and search articles'}
            </p>
          </div>

          {/* Mobile filter trigger */}
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="border-white/[0.06] text-slate-400 md:hidden"
              >
                <Filter className="mr-2 h-4 w-4" />
                Filters
              </Button>
            </SheetTrigger>
            <SheetContent className="w-72 border-white/[0.06] bg-[#060d15] p-6">
              {filtersContent}
            </SheetContent>
          </Sheet>
        </div>

        <div className="flex gap-8">
          {/* Desktop sidebar filters */}
          <aside className="hidden w-64 shrink-0 md:block">
            {filtersContent}
          </aside>

          {/* Article list */}
          <div className="min-w-0 flex-1">
            {error && (
              <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
                {error}
              </div>
            )}
            {loading ? (
              <div className="grid gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-white/[0.06] bg-[#0a1628]/60 p-5"
                  >
                    <div className="mb-3 flex gap-2">
                      <Skeleton className="h-5 w-16" />
                      <Skeleton className="h-5 w-14" />
                    </div>
                    <Skeleton className="mb-2 h-5 w-3/4" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="mt-1 h-4 w-2/3" />
                  </div>
                ))}
              </div>
            ) : articles.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.03] ring-1 ring-white/[0.06]">
                  <BookOpen className="h-6 w-6 text-slate-600" />
                </div>
                <p className="text-sm font-medium text-slate-400">No articles found</p>
                <p className="mt-1 text-xs text-slate-600">
                  Try adjusting your filters or search query
                </p>
              </div>
            ) : (
              <>
                <div className="grid gap-4">
                  {articles.map((article) => (
                    <ArticleCard key={article.id} article={article} />
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
        </div>
      </div>
    </AppLayout>
  );
}
