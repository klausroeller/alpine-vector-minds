'use client';

import { useCallback, useState } from 'react';
import { Brain } from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { SearchBar } from '@/components/copilot/search-bar';
import { ClassificationBadge } from '@/components/copilot/classification-badge';
import { ResultCard } from '@/components/copilot/result-card';
import { api, ApiError, type CopilotResponse } from '@/lib/api';

export default function CopilotPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [resultsVisible, setResultsVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async () => {
    if (!query.trim() || loading) return;
    setLoading(true);
    setResponse(null);
    setResultsVisible(false);
    setError(null);

    try {
      const data = await api.copilotAsk(query.trim());
      setResponse(data);
      // Stagger animation: show results after a brief delay
      requestAnimationFrame(() => {
        setTimeout(() => setResultsVisible(true), 50);
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [query, loading]);

  return (
    <AppLayout>
      <div className="mx-auto max-w-3xl px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Copilot
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            AI-powered search across your knowledge base
          </p>
        </div>

        {/* Search bar */}
        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={handleSubmit}
          loading={loading}
        />

        {/* Results area */}
        <div className="mt-8">
          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
              {error}
            </div>
          )}

          {response && (
            <div className="space-y-6">
              {/* Classification */}
              <ClassificationBadge
                classification={response.classification}
                visible={resultsVisible}
              />

              {/* Results */}
              {response.results.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No results found. Try rephrasing your question.
                </p>
              ) : (
                <div className="space-y-4">
                  {response.results.map((result, i) => (
                    <ResultCard
                      key={result.source_id}
                      result={result}
                      index={i}
                      visible={resultsVisible}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Empty state */}
          {!response && !loading && !error && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500/10 to-cyan-500/5 ring-1 ring-teal-500/10">
                <Brain className="h-7 w-7 text-teal-500/60" />
              </div>
              <p className="text-sm font-medium text-slate-400">
                Ask a question to get started
              </p>
              <p className="mt-1 max-w-sm text-xs text-slate-600">
                The copilot searches across knowledge articles, scripts, and ticket
                resolutions to find the most relevant answers
              </p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
