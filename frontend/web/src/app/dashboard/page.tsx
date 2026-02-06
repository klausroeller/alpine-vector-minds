'use client';

import Link from 'next/link';
import { Mountain, LogOut, Shield, User as UserIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/auth-context';
import { ProtectedRoute } from '@/components/auth/protected-route';

function DashboardContent() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#060d15] to-[#0a1220]">
      {/* Nav */}
      <nav className="border-b border-white/[0.06] bg-[#060d15]/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2 text-white/70 hover:text-white">
            <Mountain className="h-5 w-5 text-teal-400" />
            <span className="text-sm font-medium tracking-wide">Alpine Vector Minds</span>
          </Link>
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="text-slate-400 hover:text-white"
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </nav>

      {/* Content */}
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="mt-2 text-slate-400">
            Welcome back, {user?.full_name || user?.email}
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Card className="border-white/[0.06] bg-[#0a1628]/80 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500/20 to-cyan-500/10 ring-1 ring-teal-500/20">
                <UserIcon className="h-5 w-5 text-teal-400" />
              </div>
              <CardTitle className="text-lg text-white">Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Email</p>
                <p className="text-sm text-slate-300">{user?.email}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Name</p>
                <p className="text-sm text-slate-300">{user?.full_name || '—'}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Account ID
                </p>
                <p className="font-mono text-xs text-slate-400">{user?.id}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/[0.06] bg-[#0a1628]/80 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500/20 to-cyan-500/10 ring-1 ring-teal-500/20">
                <Shield className="h-5 w-5 text-teal-400" />
              </div>
              <CardTitle className="text-lg text-white">Access</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Role</p>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    user?.role === 'admin'
                      ? 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20'
                      : 'bg-teal-500/10 text-teal-400 ring-1 ring-teal-500/20'
                  }`}
                >
                  {user?.role}
                </span>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Status</p>
                <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 ring-1 ring-emerald-500/20">
                  Active
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
