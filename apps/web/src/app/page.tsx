import { Button } from '@/components/ui/button';
import { Mountain } from 'lucide-react';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="flex flex-col items-center gap-8">
        <div className="flex items-center gap-3">
          <Mountain className="h-12 w-12" />
          <h1 className="text-4xl font-bold">Alpine Vector Minds</h1>
        </div>
        <p className="text-muted-foreground text-center max-w-md">
          AI-powered application template with FastAPI backend and Next.js frontend.
        </p>
        <div className="flex gap-4">
          <Button>Get Started</Button>
          <Button variant="outline">Documentation</Button>
        </div>
      </div>
    </main>
  );
}
