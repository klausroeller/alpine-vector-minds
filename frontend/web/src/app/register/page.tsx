'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mountain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/auth-context';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(email, password, fullName || undefined);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-[#0a0f1e] via-[#0f2027] to-[#0d3b40] px-4">
      <Card className="w-full max-w-md border-white/[0.06] bg-[#0a1628]/90 backdrop-blur-sm">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500/20 to-cyan-500/10 ring-1 ring-teal-500/20">
            <Mountain className="h-6 w-6 text-teal-400" />
          </div>
          <CardTitle className="text-2xl font-bold text-white">Create account</CardTitle>
          <CardDescription className="text-slate-400">
            Get started with Alpine Vector Minds
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="fullName" className="text-slate-300">
                Full Name
              </Label>
              <Input
                id="fullName"
                type="text"
                placeholder="Jane Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="border-white/10 bg-white/[0.03] text-white placeholder:text-slate-500 focus:border-teal-500/50 focus:ring-teal-500/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-300">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="border-white/10 bg-white/[0.03] text-white placeholder:text-slate-500 focus:border-teal-500/50 focus:ring-teal-500/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-300">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="border-white/10 bg-white/[0.03] text-white placeholder:text-slate-500 focus:border-teal-500/50 focus:ring-teal-500/20"
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-teal-500 to-teal-600 font-semibold text-white shadow-lg shadow-teal-500/20 hover:from-teal-400 hover:to-teal-500"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-teal-400 hover:text-teal-300">
              Sign in
            </Link>
          </p>
          <p className="mt-2 text-center text-sm text-slate-500">
            <Link href="/" className="hover:text-slate-300">
              &larr; Back to home
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
