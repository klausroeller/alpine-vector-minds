'use client';

import { useRef, useCallback } from 'react';
import { Send, Zap, FlaskConical } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type CopilotMode = 'quick' | 'research';

interface SearchBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  mode: CopilotMode;
  onModeChange: (mode: CopilotMode) => void;
}

export function SearchBar({ value, onChange, onSubmit, loading, mode, onModeChange }: SearchBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        onSubmit();
      }
    },
    [onSubmit]
  );

  const isResearch = mode === 'research';

  return (
    <div className="relative">
      {/* Mode toggle */}
      <div className="mb-2 flex gap-1.5">
        <button
          type="button"
          onClick={() => onModeChange('quick')}
          className={cn(
            'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all',
            !isResearch
              ? 'bg-teal-500/15 text-teal-400 ring-1 ring-teal-500/30'
              : 'text-slate-500 hover:text-slate-400'
          )}
        >
          <Zap className="h-3 w-3" />
          Quick Search
        </button>
        <button
          type="button"
          onClick={() => onModeChange('research')}
          className={cn(
            'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all',
            isResearch
              ? 'bg-violet-500/15 text-violet-400 ring-1 ring-violet-500/30'
              : 'text-slate-500 hover:text-slate-400'
          )}
        >
          <FlaskConical className="h-3 w-3" />
          Deep Research
        </button>
      </div>

      {/* Glow effect */}
      <div
        className={cn(
          'absolute -inset-1 rounded-2xl opacity-60 blur-xl',
          isResearch
            ? 'bg-gradient-to-r from-violet-500/20 via-purple-500/20 to-violet-500/20'
            : 'bg-gradient-to-r from-teal-500/20 via-cyan-500/20 to-teal-500/20'
        )}
      />

      <div className="relative rounded-xl border border-white/[0.08] bg-[#0a1628]/90 p-1 shadow-2xl shadow-teal-500/5 backdrop-blur-sm">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isResearch
              ? 'Ask a complex question for deep multi-source research...'
              : 'Ask a question about your support knowledge...'
          }
          rows={3}
          className="resize-none border-0 bg-transparent text-[15px] text-slate-200 placeholder:text-slate-600 focus-visible:ring-0"
        />

        <div className="flex items-center justify-between px-3 pb-2">
          <span className="text-[11px] text-slate-700">
            {navigator.platform?.includes('Mac') ? '\u2318' : 'Ctrl'}+Enter to submit
          </span>
          <Button
            onClick={onSubmit}
            disabled={!value.trim() || loading}
            size="sm"
            className={cn(
              'text-sm font-medium text-white shadow-lg transition-all disabled:opacity-40',
              isResearch
                ? 'bg-gradient-to-r from-violet-600 to-purple-600 shadow-violet-500/20 hover:from-violet-500 hover:to-purple-500 hover:shadow-violet-500/30'
                : 'bg-gradient-to-r from-teal-600 to-cyan-600 shadow-teal-500/20 hover:from-teal-500 hover:to-cyan-500 hover:shadow-teal-500/30'
            )}
          >
            {loading ? (
              <div className="mr-2 h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              <Send className="mr-1.5 h-3.5 w-3.5" />
            )}
            {loading
              ? (isResearch ? 'Researching...' : 'Searching...')
              : (isResearch ? 'Research' : 'Ask')}
          </Button>
        </div>
      </div>
    </div>
  );
}
