import type { Metadata, Viewport } from 'next'
import { Geist, JetBrains_Mono } from 'next/font/google'
import Script from 'next/script'
import { Analytics } from '@vercel/analytics/next'
import { AppShell } from '@/components/shell/app-shell'
import './globals.css'

const geistSans = Geist({
  subsets: ['latin'],
  variable: '--font-geist-sans',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  adjustFontFallback: false,
  fallback: ['ui-monospace', 'Menlo', 'Consolas', 'DejaVu Sans Mono', 'monospace'],
})

export const metadata: Metadata = {
  title: 'Kuber OS — Autonomous AI Finance Controller & Settlement Assurance',
  description:
    'Multi-Source Financial Reconciliation, Statutory Tax Assurance & Autonomous Nodal Recovery. Built for Razorpay AI Buildathon 2026 (Track 04: AI Finance Controller).',
}

export const viewport: Viewport = {
  colorScheme: 'dark light',
  themeColor: [
    { media: '(prefers-color-scheme: dark)', color: '#090d16' },
    { media: '(prefers-color-scheme: light)', color: '#f8fafc' },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <head>
        <Script
          id="theme-initializer"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
(function () {
  try {
    var stored = localStorage.getItem("apex-theme");
    var theme = (stored === "mission-control" || stored === "dark") ? "mission-control" : "light";
    document.documentElement.dataset.theme = theme;
    if (theme === "light") {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
    } else {
      document.documentElement.classList.remove("light");
      document.documentElement.classList.add("dark");
    }
  } catch (e) {
    document.documentElement.dataset.theme = "light";
    document.documentElement.classList.add("light");
  }
})();
`,
          }}
        />
      </head>
      <body className="font-sans antialiased bg-background text-foreground min-h-screen transition-colors duration-200">
        <AppShell>{children}</AppShell>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
