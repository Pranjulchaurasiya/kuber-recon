import type { Metadata, Viewport } from 'next'
import { Geist, JetBrains_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { Sidebar } from '@/components/shell/sidebar'
import { Topbar } from '@/components/shell/topbar'
import './globals.css'

const geistSans = Geist({
  subsets: ['latin'],
  variable: '--font-geist-sans',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  // Disable the auto-generated covering fallback face so glyphs missing from
  // the loaded subset (e.g. ₹ / U+20B9) fall through per-glyph to the mono
  // chain below instead of rendering as tofu.
  adjustFontFallback: false,
  fallback: ['ui-monospace', 'Menlo', 'Consolas', 'DejaVu Sans Mono', 'monospace'],
})

export const metadata: Metadata = {
  title: 'KuberRecon — Financial Integrity OS',
  description:
    'Autonomous Financial Integrity Operating System. Every rupee tracked to its statutory root; zero tax lost, zero math guessed.',
  generator: 'v0.app',
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#0b0e14',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`dark bg-background ${geistSans.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased">
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <Topbar />
            <main className="flex-1">{children}</main>
          </div>
        </div>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
