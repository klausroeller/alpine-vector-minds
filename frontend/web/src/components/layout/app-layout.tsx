'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Mountain,
  LayoutDashboard,
  MessageSquareText,
  BookOpen,
  GraduationCap,
  LogOut,
  Menu,
  ChevronDown,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useAuth } from '@/contexts/auth-context';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/copilot', label: 'Copilot', icon: MessageSquareText },
  { href: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
  { href: '/learning', label: 'Learning Feed', icon: GraduationCap },
];

function SidebarContent({ pathname }: { pathname: string }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2.5 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-cyan-400">
          <Mountain className="h-4 w-4 text-[#060d15]" />
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-white">
          SupportMind
        </span>
      </div>

      {/* Nav */}
      <nav className="mt-4 flex-1 space-y-1 px-3">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150',
                isActive
                  ? 'border-l-2 border-teal-400 bg-teal-500/10 text-teal-400'
                  : 'border-l-2 border-transparent text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'
              )}
            >
              <Icon
                className={cn(
                  'h-[18px] w-[18px] transition-colors',
                  isActive ? 'text-teal-400' : 'text-slate-500 group-hover:text-slate-400'
                )}
              />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="border-t border-white/[0.06] p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-white/[0.04]">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-teal-600 to-cyan-500 text-xs font-semibold text-white">
                {(user?.full_name || user?.email || '?')[0].toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-200">
                  {user?.full_name || 'User'}
                </p>
                <p className="truncate text-xs text-slate-500">{user?.email}</p>
              </div>
              <ChevronDown className="h-4 w-4 shrink-0 text-slate-500" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="w-56 border-white/[0.06] bg-[#0c1a2a]"
          >
            <DropdownMenuItem
              onClick={logout}
              className="cursor-pointer text-slate-400 focus:bg-white/[0.06] focus:text-white"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

function AppLayoutInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-[#060d15]">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-white/[0.06] bg-[#060d15] md:block">
        <SidebarContent pathname={pathname} />
      </aside>

      {/* Mobile header + sheet */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center gap-3 border-b border-white/[0.06] bg-[#060d15] px-4 md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-slate-400">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="left"
              className="w-64 border-white/[0.06] bg-[#060d15] p-0"
            >
              <SidebarContent pathname={pathname} />
            </SheetContent>
          </Sheet>
          <div className="flex items-center gap-2">
            <Mountain className="h-4 w-4 text-teal-400" />
            <span className="text-sm font-semibold text-white">SupportMind</span>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto bg-gradient-to-b from-[#060d15] to-[#0a1220]">
          {children}
        </main>
      </div>
    </div>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayoutInner>{children}</AppLayoutInner>
    </ProtectedRoute>
  );
}
