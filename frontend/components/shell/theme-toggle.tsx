'use client'

import { useEffect, useState } from 'react'
import { Sun, Moon } from 'lucide-react'

export function ThemeToggle() {
  const [isLight, setIsLight] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    try {
      const stored = localStorage.getItem('apex-theme')
      if (stored === 'light' || document.documentElement.classList.contains('light')) {
        setIsLight(true)
      } else {
        setIsLight(false)
      }
    } catch {
      setIsLight(false)
    }
  }, [])

  const toggleTheme = () => {
    const nextIsLight = !isLight
    setIsLight(nextIsLight)

    if (nextIsLight) {
      document.documentElement.dataset.theme = 'light'
      document.documentElement.classList.remove('dark')
      document.documentElement.classList.add('light')
      try {
        localStorage.setItem('apex-theme', 'light')
      } catch {}
    } else {
      document.documentElement.dataset.theme = 'mission-control'
      document.documentElement.classList.remove('light')
      document.documentElement.classList.add('dark')
      try {
        localStorage.setItem('apex-theme', 'mission-control')
      } catch {}
    }
  }

  if (!mounted) {
    return (
      <div className="h-8 w-8 rounded-lg border border-border bg-panel opacity-50" />
    )
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-panel px-2.5 py-1.5 text-xs font-semibold text-foreground shadow-sm transition-all hover:bg-accent hover:border-primary/40 focus:outline-none"
      aria-label={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
      title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
    >
      {isLight ? (
        <>
          <Moon className="h-4 w-4 text-primary" />
          <span className="font-mono text-xs hidden sm:inline">Dark</span>
        </>
      ) : (
        <>
          <Sun className="h-4 w-4 text-gold" />
          <span className="font-mono text-xs hidden sm:inline">Light</span>
        </>
      )}
    </button>
  )
}

