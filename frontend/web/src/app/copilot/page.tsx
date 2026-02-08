'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Brain } from 'lucide-react';
import { AppLayout } from '@/components/layout/app-layout';
import { SearchBar, type CopilotMode } from '@/components/copilot/search-bar';
import { ClassificationBadge } from '@/components/copilot/classification-badge';
import { ResultCard } from '@/components/copilot/result-card';
import { ResearchReportView } from '@/components/copilot/research-report';
import { api, ApiError, type CopilotResponse, type CopilotResearchResponse } from '@/lib/api';

function CopilotContent() {
  const searchParams = useSearchParams();
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<CopilotMode>('quick');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [researchResponse, setResearchResponse] = useState<CopilotResearchResponse | null>(null);
  const [resultsVisible, setResultsVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Record<string, 'up' | 'down'>>({});
  const autoSearchTriggered = useRef(false);

  const handleFeedback = useCallback((resultId: string, rank: number, helpful: boolean) => {
    setFeedback((prev) => ({ ...prev, [resultId]: helpful ? 'up' : 'down' }));
    // Fire-and-forget
    api.submitFeedback({
      question_text: query,
      classification: response?.classification.answer_type,
      result_id: resultId,
      result_rank: rank,
      helpful,
    }).catch(() => {});
  }, [query, response]);

  const handleSubmit = useCallback(async () => {
    if (!query.trim() || loading) return;
    setLoading(true);
    setResponse(null);
    setResearchResponse(null);
    setResultsVisible(false);
    setError(null);
    setFeedback({});

    try {
      if (mode === 'research') {
        const data = await api.copilotResearch(query.trim());
        setResearchResponse(data);
      } else {
        const data = await api.copilotAsk(query.trim());
        setResponse(data);
      }
      requestAnimationFrame(() => {
        setTimeout(() => setResultsVisible(true), 50);
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.debugMessage : err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [query, loading, mode]);

  // Pre-fill and auto-search from ?q= URL param
  useEffect(() => {
    const q = searchParams.get('q');
    if (q && !autoSearchTriggered.current) {
      autoSearchTriggered.current = true;
      setQuery(q);
    }
  }, [searchParams]);

  // Trigger search once query is set from URL param
  useEffect(() => {
    if (autoSearchTriggered.current && query && !loading && !response && !researchResponse) {
      handleSubmit();
    }
    // Only run when query changes after auto-fill
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  // Determine what to render
  const hasQuickResponse = response !== null;
  const hasResearchResponse = researchResponse !== null;
  const hasAnyResponse = hasQuickResponse || hasResearchResponse;

  // Research response that fell back to simple mode
  const researchSimple = researchResponse?.mode === 'simple';

  return (
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
        mode={mode}
        onModeChange={setMode}
      />

      {/* Results area */}
      <div className="mt-8">
        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Quick search results */}
        {hasQuickResponse && (
          <div className="space-y-6">
            <ClassificationBadge
              classification={response.classification}
              visible={resultsVisible}
            />
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
                    questionText={query}
                    classification={response.classification.answer_type}
                    feedbackGiven={feedback[result.source_id] ?? null}
                    onFeedback={handleFeedback}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Research response — simple fallback */}
        {hasResearchResponse && researchSimple && researchResponse.classification && (
          <div className="space-y-6">
            <ClassificationBadge
              classification={researchResponse.classification}
              visible={resultsVisible}
            />
            {(!researchResponse.results || researchResponse.results.length === 0) ? (
              <p className="text-sm text-slate-500">
                No results found. Try rephrasing your question.
              </p>
            ) : (
              <div className="space-y-4">
                {researchResponse.results.map((result, i) => (
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

        {/* Research response — full report */}
        {hasResearchResponse && !researchSimple && (
          <ResearchReportView response={researchResponse} visible={resultsVisible} />
        )}

        {/* Empty state */}
        {!hasAnyResponse && !loading && !error && (
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
  );
}

export default function CopilotPage() {
  return (
    <AppLayout>
      <Suspense>
        <CopilotContent />
      </Suspense>
    </AppLayout>
  );
}
