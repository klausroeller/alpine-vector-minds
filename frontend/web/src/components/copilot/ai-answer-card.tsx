'use client';

import { useState } from 'react';
import { Sparkles, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AIAnswer } from '@/lib/api';

interface AIAnswerCardProps {
  answer: AIAnswer;
  visible: boolean;
}

export function AIAnswerCard({ answer, visible }: AIAnswerCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(answer.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Turn [SOURCE-ID] references into styled badges
  const renderText = (text: string) => {
    const parts = text.split(/(\[[A-Z]+-\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/^\[([A-Z]+-\d+)\]$/);
      if (match) {
        return (
          <span
            key={i}
            className="inline-flex items-center rounded bg-teal-500/15 px-1.5 py-0.5 font-mono text-xs font-semibold text-teal-300"
          >
            {match[1]}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div
      className={cn(
        'transform transition-all duration-500',
        visible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0',
      )}
    >
      <div className="relative overflow-hidden rounded-xl border border-teal-500/20 bg-gradient-to-br from-teal-500/[0.08] to-cyan-500/[0.04]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-teal-500/10 px-5 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-teal-400" />
            <span className="text-sm font-semibold text-teal-300">AI Answer</span>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-slate-400 transition-colors hover:bg-white/[0.06] hover:text-slate-200"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                Copy
              </>
            )}
          </button>
        </div>

        {/* Answer body */}
        <div className="px-5 py-4">
          <p className="text-[15px] leading-relaxed text-slate-200">
            {renderText(answer.text)}
          </p>
        </div>

        {/* Source footer */}
        {answer.source_ids.length > 0 && (
          <div className="flex items-center gap-2 border-t border-teal-500/10 px-5 py-2.5">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-600">
              Sources
            </span>
            {answer.source_ids.map((id) => (
              <span
                key={id}
                className="rounded bg-white/[0.04] px-2 py-0.5 font-mono text-xs text-teal-400/80 ring-1 ring-white/[0.06]"
              >
                {id}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
