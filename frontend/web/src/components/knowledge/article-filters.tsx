'use client';

import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface ArticleFiltersProps {
  search: string;
  onSearchChange: (v: string) => void;
  sourceType: string;
  onSourceTypeChange: (v: string) => void;
  category: string;
  onCategoryChange: (v: string) => void;
  status: string;
  onStatusChange: (v: string) => void;
  categories: string[];
}

export function ArticleFilters({
  search,
  onSearchChange,
  sourceType,
  onSourceTypeChange,
  category,
  onCategoryChange,
  status,
  onStatusChange,
  categories,
}: ArticleFiltersProps) {
  return (
    <div className="space-y-5">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <Input
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search articles..."
          className="border-white/[0.06] bg-[#0a1628]/60 pl-9 text-sm text-slate-300 placeholder:text-slate-600 focus:border-teal-500/30 focus:ring-teal-500/20"
        />
      </div>

      {/* Source type tabs */}
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-600">
          Source
        </p>
        <Tabs value={sourceType} onValueChange={onSourceTypeChange}>
          <TabsList className="w-full bg-white/[0.03]">
            <TabsTrigger value="all" className="flex-1 text-xs">All</TabsTrigger>
            <TabsTrigger value="seed" className="flex-1 text-xs">Seed</TabsTrigger>
            <TabsTrigger value="synthetic" className="flex-1 text-xs">Synthetic</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Category select */}
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-600">
          Category
        </p>
        <Select value={category} onValueChange={onCategoryChange}>
          <SelectTrigger className="border-white/[0.06] bg-[#0a1628]/60 text-sm text-slate-300">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent className="border-white/[0.06] bg-[#0c1a2a] text-slate-300">
            <SelectItem value="all" className="text-slate-300 focus:bg-white/[0.08] focus:text-white">All categories</SelectItem>
            {categories.map((cat) => (
              <SelectItem key={cat} value={cat} className="text-slate-300 focus:bg-white/[0.08] focus:text-white">
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Status select */}
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-600">
          Status
        </p>
        <Select value={status} onValueChange={onStatusChange}>
          <SelectTrigger className="border-white/[0.06] bg-[#0a1628]/60 text-sm text-slate-300">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent className="border-white/[0.06] bg-[#0c1a2a] text-slate-300">
            <SelectItem value="all" className="text-slate-300 focus:bg-white/[0.08] focus:text-white">All statuses</SelectItem>
            <SelectItem value="ACTIVE" className="text-slate-300 focus:bg-white/[0.08] focus:text-white">Active</SelectItem>
            <SelectItem value="DRAFT" className="text-slate-300 focus:bg-white/[0.08] focus:text-white">Draft</SelectItem>
            <SelectItem value="ARCHIVED" className="text-slate-300 focus:bg-white/[0.08] focus:text-white">Archived</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
