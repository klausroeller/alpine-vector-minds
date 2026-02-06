import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Mountain, Brain, Shield, Cloud, ChevronDown } from 'lucide-react';

function MountainSilhouette() {
  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
      {/* Sky gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0f1e] via-[#0f2027] to-[#0d3b40]" />

      {/* Stars */}
      <div className="absolute inset-0 opacity-60">
        {[...Array(40)].map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full bg-white animate-pulse"
            style={{
              width: `${1 + Math.random() * 2}px`,
              height: `${1 + Math.random() * 2}px`,
              top: `${Math.random() * 40}%`,
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 4}s`,
              animationDuration: `${2 + Math.random() * 3}s`,
            }}
          />
        ))}
      </div>

      {/* Aurora / northern lights glow */}
      <div
        className="absolute top-0 left-1/4 w-1/2 h-1/3 opacity-20 blur-3xl"
        style={{
          background: 'radial-gradient(ellipse at center, #0d9488 0%, #06b6d4 40%, transparent 70%)',
        }}
      />

      {/* Far mountain range */}
      <svg
        className="absolute bottom-0 w-full"
        viewBox="0 0 1440 500"
        preserveAspectRatio="none"
        style={{ height: '55%' }}
      >
        <path
          d="M0,500 L0,280 Q120,180 200,240 Q280,140 360,200 Q440,100 520,180 Q600,60 720,160 Q800,80 900,140 Q980,40 1060,120 Q1140,60 1200,140 Q1280,80 1360,160 Q1400,140 1440,180 L1440,500 Z"
          fill="#0f1f2e"
          opacity="0.7"
        />
        {/* Snow caps on far range */}
        <path
          d="M520,180 Q560,155 600,170 Q570,130 520,180 Z M900,140 Q930,120 960,135 Q935,105 900,140 Z M1060,120 Q1085,100 1110,115 Q1088,88 1060,120 Z"
          fill="rgba(255,255,255,0.15)"
        />
      </svg>

      {/* Mid mountain range */}
      <svg
        className="absolute bottom-0 w-full"
        viewBox="0 0 1440 400"
        preserveAspectRatio="none"
        style={{ height: '45%' }}
      >
        <path
          d="M0,400 L0,220 Q80,180 160,200 Q240,100 340,180 Q420,60 540,140 Q620,40 720,100 Q800,20 920,80 Q1000,40 1100,120 Q1200,60 1300,100 Q1360,80 1440,120 L1440,400 Z"
          fill="#0b1926"
          opacity="0.85"
        />
        {/* Snow caps on mid range */}
        <path
          d="M340,180 Q380,150 420,170 Q390,120 340,180 Z M720,100 Q755,78 790,95 Q760,55 720,100 Z M920,80 Q950,60 980,78 Q955,40 920,80 Z"
          fill="rgba(255,255,255,0.2)"
        />
      </svg>

      {/* Near mountain range with forest */}
      <svg
        className="absolute bottom-0 w-full"
        viewBox="0 0 1440 320"
        preserveAspectRatio="none"
        style={{ height: '35%' }}
      >
        <defs>
          <linearGradient id="nearMountain" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#091420" />
            <stop offset="100%" stopColor="#060d15" />
          </linearGradient>
        </defs>
        <path
          d="M0,320 L0,200 Q60,160 120,180 Q180,80 280,140 Q360,60 460,100 Q540,40 640,80 Q720,20 840,60 Q920,30 1020,80 Q1120,40 1200,60 Q1280,40 1360,80 L1440,60 L1440,320 Z"
          fill="url(#nearMountain)"
        />
      </svg>

      {/* Fog layer */}
      <div
        className="absolute bottom-[15%] left-0 right-0 h-32 opacity-30"
        style={{
          background: 'linear-gradient(to bottom, transparent, rgba(13,148,136,0.15), transparent)',
        }}
      />
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <div className="group relative">
      <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-br from-teal-500/20 to-cyan-500/20 opacity-0 blur transition-all duration-500 group-hover:opacity-100" />
      <div className="relative flex flex-col gap-4 rounded-2xl border border-white/[0.06] bg-[#0a1628]/80 p-8 backdrop-blur-sm transition-all duration-500 group-hover:border-teal-500/20 group-hover:bg-[#0a1628]/90">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500/20 to-cyan-500/10 ring-1 ring-teal-500/20">
          <Icon className="h-6 w-6 text-teal-400" />
        </div>
        <h3 className="text-lg font-semibold tracking-tight text-white/90">{title}</h3>
        <p className="text-sm leading-relaxed text-slate-400">{description}</p>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <main className="relative bg-[#060d15]">
      {/* ── Hero Section ── */}
      <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden">
        <MountainSilhouette />

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center gap-8 px-6 text-center">
          {/* Logo mark */}
          <div className="flex items-center gap-3 rounded-full border border-white/[0.08] bg-white/[0.03] px-5 py-2.5 backdrop-blur-md">
            <Mountain className="h-5 w-5 text-teal-400" />
            <span className="text-sm font-medium tracking-widest text-white/70 uppercase">
              Alpine Vector Minds
            </span>
          </div>

          {/* Heading */}
          <h1 className="max-w-4xl text-5xl font-bold leading-[1.1] tracking-tight text-white sm:text-6xl md:text-7xl lg:text-8xl">
            <span className="block">Search at the</span>
            <span
              className="block bg-gradient-to-r from-teal-300 via-cyan-300 to-teal-400 bg-clip-text text-transparent"
              style={{
                filter: 'drop-shadow(0 0 40px rgba(13,148,136,0.3))',
              }}
            >
              speed of thought
            </span>
          </h1>

          {/* Tagline */}
          <p className="max-w-xl text-lg leading-relaxed text-slate-400 sm:text-xl">
            AI-powered vector search, built for the mountains of data.
            Navigate complexity with precision.
          </p>

          {/* CTAs */}
          <div className="flex flex-col gap-4 pt-4 sm:flex-row">
            <Button
              asChild
              size="lg"
              className="h-12 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 px-8 text-base font-semibold text-white shadow-lg shadow-teal-500/20 transition-all hover:from-teal-400 hover:to-teal-500 hover:shadow-teal-500/30"
            >
              <Link href="/login">Sign In</Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="h-12 rounded-xl border-white/10 bg-white/[0.03] px-8 text-base font-semibold text-white/80 backdrop-blur-sm transition-all hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
            >
              <a href="#features">Learn More</a>
            </Button>
          </div>
        </div>

        {/* Scroll indicator */}
        <a
          href="#features"
          className="absolute bottom-8 z-10 flex flex-col items-center gap-2 text-white/30 transition-colors hover:text-white/60"
        >
          <span className="text-xs font-medium tracking-widest uppercase">Explore</span>
          <ChevronDown className="h-4 w-4 animate-bounce" />
        </a>
      </section>

      {/* ── Features Section ── */}
      <section
        id="features"
        className="relative border-t border-white/[0.04] bg-gradient-to-b from-[#060d15] to-[#0a1220]"
      >
        <div className="mx-auto max-w-5xl px-6 py-32">
          <div className="mb-16 text-center">
            <p className="mb-3 text-sm font-medium tracking-widest text-teal-400/80 uppercase">
              Capabilities
            </p>
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Built for serious workloads
            </h2>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={Brain}
              title="Vector Search"
              description="Semantic search powered by state-of-the-art embeddings. Find meaning, not just keywords, across millions of documents."
            />
            <FeatureCard
              icon={Shield}
              title="Role-Based Access"
              description="Fine-grained permissions with JWT authentication. Admin and user roles keep your data secure and organized."
            />
            <FeatureCard
              icon={Cloud}
              title="Cloud Native"
              description="Containerized deployment on AWS with automated SSL, database backups, and infrastructure as code via Terraform."
            />
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/[0.04] bg-[#060d15]">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-8">
          <div className="flex items-center gap-2 text-white/30">
            <Mountain className="h-4 w-4" />
            <span className="text-sm">Alpine Vector Minds</span>
          </div>
          <p className="text-sm text-white/20">&copy; {new Date().getFullYear()}</p>
        </div>
      </footer>
    </main>
  );
}
