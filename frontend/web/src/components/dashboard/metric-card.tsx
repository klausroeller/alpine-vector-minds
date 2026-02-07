'use client';

import type { LucideIcon } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: number | string;
  gradient: string;
  loading?: boolean;
}

export function MetricCard({ icon: Icon, label, value, gradient, loading }: MetricCardProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-white/[0.06] bg-[#0a1628]/80 p-5">
        <div className="flex items-center gap-4">
          <Skeleton className="h-11 w-11 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-7 w-16" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group rounded-xl border border-white/[0.06] bg-[#0a1628]/80 p-5 transition-all duration-300 hover:border-white/[0.1] hover:bg-[#0a1628]">
      <div className="flex items-center gap-4">
        <div
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ring-1 ring-white/[0.06]',
            gradient
          )}
        >
          <Icon className="h-5 w-5 text-white/90" />
        </div>
        <div>
          <p className="text-2xl font-bold tracking-tight text-white">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          <p className="text-sm text-slate-500">{label}</p>
        </div>
      </div>
    </div>
  );
}
