'use client';

import { ScrollText, BookOpen, Ticket } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Classification } from '@/lib/api';

interface ClassificationBadgeProps {
  classification: Classification;
  visible: boolean;
}

const TYPE_CONFIG: Record<string, {
  label: string;
  icon: React.ElementType;
  className: string;
}> = {
  SCRIPT: {
    label: 'Script',
    icon: ScrollText,
    className: 'from-violet-500/20 to-purple-500/10 text-violet-400 ring-violet-500/20',
  },
  KB: {
    label: 'Knowledge Base',
    icon: BookOpen,
    className: 'from-cyan-500/20 to-teal-500/10 text-cyan-400 ring-cyan-500/20',
  },
  TICKET_RESOLUTION: {
    label: 'Ticket Resolution',
    icon: Ticket,
    className: 'from-amber-500/20 to-orange-500/10 text-amber-400 ring-amber-500/20',
  },
};

export function ClassificationBadge({ classification, visible }: ClassificationBadgeProps) {
  const config = TYPE_CONFIG[classification.answer_type] ?? TYPE_CONFIG.KB;
  const Icon = config.icon;
  const confidencePct = Math.round(classification.confidence * 100);

  return (
    <div
      className={cn(
        'transform transition-all duration-500',
        visible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'
      )}
    >
      <div
        className={cn(
          'inline-flex items-center gap-3 rounded-xl bg-gradient-to-r px-4 py-2.5 ring-1',
          config.className
        )}
      >
        <Icon className="h-4 w-4" />
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{config.label}</span>
            <span className="rounded-full bg-white/10 px-2 py-0.5 text-[11px] font-semibold">
              {confidencePct}%
            </span>
          </div>
          {classification.reasoning && (
            <p className="mt-0.5 text-xs opacity-60">{classification.reasoning}</p>
          )}
        </div>
      </div>
    </div>
  );
}
