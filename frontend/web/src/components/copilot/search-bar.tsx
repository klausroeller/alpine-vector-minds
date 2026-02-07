'use client';

import { useRef, useCallback } from 'react';
import { Send } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

interface SearchBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading?: boolean;
}

export function SearchBar({ value, onChange, onSubmit, loading }: SearchBarProps) {
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

  return (
    <div className="relative">
      {/* Glow effect */}
      <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-teal-500/20 via-cyan-500/20 to-teal-500/20 opacity-60 blur-xl" />

      <div className="relative rounded-xl border border-white/[0.08] bg-[#0a1628]/90 p-1 shadow-2xl shadow-teal-500/5 backdrop-blur-sm">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your support knowledge..."
          rows={3}
          className="resize-none border-0 bg-transparent text-[15px] text-slate-200 placeholder:text-slate-600 focus-visible:ring-0"
        />

        <div className="flex items-center justify-between px-3 pb-2">
          <span className="text-[11px] text-slate-700">
            {navigator.platform?.includes('Mac') ? '⌘' : 'Ctrl'}+Enter to submit
          </span>
          <Button
            onClick={onSubmit}
            disabled={!value.trim() || loading}
            size="sm"
            className="bg-gradient-to-r from-teal-600 to-cyan-600 text-sm font-medium text-white shadow-lg shadow-teal-500/20 transition-all hover:from-teal-500 hover:to-cyan-500 hover:shadow-teal-500/30 disabled:opacity-40"
          >
            {loading ? (
              <div className="mr-2 h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              <Send className="mr-1.5 h-3.5 w-3.5" />
            )}
            {loading ? 'Searching...' : 'Ask'}
          </Button>
        </div>
      </div>
    </div>
  );
}
