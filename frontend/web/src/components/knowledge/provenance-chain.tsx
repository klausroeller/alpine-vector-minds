'use client';

import { Ticket, MessagesSquare, ScrollText } from 'lucide-react';
import type { LineageEntry, ProvenanceInfo } from '@/lib/api';
import { cn } from '@/lib/utils';

type ChainStep = {
  label: string;
  id: string | null;
  icon: React.ElementType;
  color: string;
};

function buildChainFromLineage(lineage: LineageEntry[]): ChainStep[] {
  const steps: ChainStep[] = [];
  for (const entry of lineage) {
    const rel = (entry.relationship ?? '').toLowerCase();
    if (rel.includes('ticket') || rel.includes('trigger')) {
      steps.push({
        label: 'Ticket',
        id: entry.source_id,
        icon: Ticket,
        color: 'text-amber-400 bg-amber-500/10 ring-amber-500/20',
      });
    } else if (rel.includes('conversation') || rel.includes('chat')) {
      steps.push({
        label: 'Conversation',
        id: entry.source_id,
        icon: MessagesSquare,
        color: 'text-cyan-400 bg-cyan-500/10 ring-cyan-500/20',
      });
    } else if (rel.includes('script')) {
      steps.push({
        label: 'Script',
        id: entry.source_id,
        icon: ScrollText,
        color: 'text-violet-400 bg-violet-500/10 ring-violet-500/20',
      });
    } else {
      steps.push({
        label: entry.relationship ?? 'Source',
        id: entry.source_id,
        icon: Ticket,
        color: 'text-slate-400 bg-slate-500/10 ring-slate-500/20',
      });
    }
  }
  return steps;
}

function buildChainFromProvenance(prov: ProvenanceInfo): ChainStep[] {
  const steps: ChainStep[] = [];
  if (prov.created_from_ticket) {
    steps.push({
      label: 'Ticket',
      id: prov.created_from_ticket,
      icon: Ticket,
      color: 'text-amber-400 bg-amber-500/10 ring-amber-500/20',
    });
  }
  if (prov.created_from_conversation) {
    steps.push({
      label: 'Conversation',
      id: prov.created_from_conversation,
      icon: MessagesSquare,
      color: 'text-cyan-400 bg-cyan-500/10 ring-cyan-500/20',
    });
  }
  if (prov.references_script) {
    steps.push({
      label: 'Script',
      id: prov.references_script,
      icon: ScrollText,
      color: 'text-violet-400 bg-violet-500/10 ring-violet-500/20',
    });
  }
  return steps;
}

interface ProvenanceChainProps {
  lineage?: LineageEntry[];
  provenance?: ProvenanceInfo;
}

export function ProvenanceChain({ lineage, provenance }: ProvenanceChainProps) {
  const steps = lineage
    ? buildChainFromLineage(lineage)
    : provenance
      ? buildChainFromProvenance(provenance)
      : [];

  if (steps.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {steps.map((step, i) => {
        const Icon = step.icon;
        return (
          <div key={i} className="flex items-center gap-2">
            {i > 0 && (
              <div className="h-px w-6 border-t border-dashed border-slate-700" />
            )}
            <div
              className={cn(
                'flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium ring-1',
                step.color
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{step.label}</span>
              {step.id && (
                <span className="font-mono text-[10px] opacity-60">
                  {step.id.slice(0, 8)}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
