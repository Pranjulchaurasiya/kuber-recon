import Link from 'next/link'
import { ShieldAlert, Terminal, Home } from 'lucide-react'

export default function NotFound() {
  return (
    <main className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Background radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-md w-full text-center space-y-6 rounded-2xl border border-border bg-panel/80 backdrop-blur-xl p-8 shadow-2xl">
        {/* Sandbox Status Header */}
        <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-mono font-medium text-amber-500">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
          RAZORPAY SANDBOX SIMULATION
        </div>

        {/* 404 Graphic */}
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-danger/10 text-danger border border-danger/20">
          <ShieldAlert className="h-8 w-8" />
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight font-mono text-foreground">404</h1>
          <h2 className="text-base font-bold text-foreground">Route Invariant Not Found</h2>
          <p className="text-xs text-muted-foreground leading-relaxed">
            The requested financial endpoint or dashboard surface does not exist in the active Kuber OS deployment.
          </p>
        </div>

        {/* Navigation Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link
            href="/console"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold text-primary-foreground shadow-lg shadow-primary/25 hover:bg-primary/90 transition-all font-mono"
          >
            <Terminal className="h-4 w-4" />
            Open Console
          </Link>
          <Link
            href="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-background px-5 py-2.5 text-xs font-bold text-muted-foreground hover:text-foreground hover:bg-panel transition-all font-mono"
          >
            <Home className="h-4 w-4" />
            Home
          </Link>
        </div>
      </div>
    </main>
  )
}
