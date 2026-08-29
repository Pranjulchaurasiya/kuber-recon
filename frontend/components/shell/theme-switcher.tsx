'use client'

import { useEffect, useState, useRef } from 'react'
import { Palette, Check, ChevronDown } from 'lucide-react'

export type ThemeType = 'mission-control' | 'razorpay-blue' | 'terminal-dark' | 'blueprint' | 'vscode-dark' | 'light'

interface ThemeOption {
  id: ThemeType
  name: string
  swatch: string
  border: string
  mode: 'dark' | 'light'
}

const THEMES: ThemeOption[] = [
  { id: 'mission-control', name: 'Mission Control', swatch: 'bg-[#0f1626] border-sky-400', border: '#38bdf8', mode: 'dark' },
  { id: 'razorpay-blue', name: 'Razorpay Blue', swatch: 'bg-[#07132c] border-blue-500', border: '#3395ff', mode: 'dark' },
  { id: 'terminal-dark', name: 'Terminal Dark', swatch: 'bg-[#000000] border-emerald-500', border: '#10b981', mode: 'dark' },
  { id: 'blueprint', name: 'Blueprint CAD', swatch: 'bg-[#0a2145] border-cyan-400', border: '#38bdf8', mode: 'dark' },
  { id: 'vscode-dark', name: 'VS Code Dark', swatch: 'bg-[#1f1f1f] border-amber-400', border: '#dcdcaa', mode: 'dark' },
  { id: 'light', name: 'Crisp Light', swatch: 'bg-[#ffffff] border-slate-400', border: '#0284c7', mode: 'light' },
]

export function ThemeSwitcher() {
  const [theme, setTheme] = useState<ThemeType>('mission-control')
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    try {
      const stored = localStorage.getItem('apex-theme') as ThemeType
      if (stored && THEMES.some((t) => t.id === stored)) {
        setTheme(stored)
        applyTheme(stored)
      } else {
        applyTheme('mission-control')
      }
    } catch {
      applyTheme('mission-control')
    }
  }, [])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function applyTheme(newTheme: ThemeType) {
    document.documentElement.dataset.theme = newTheme
    if (newTheme === 'light') {
      document.documentElement.classList.remove('dark')
      document.documentElement.classList.add('light')
    } else {
      document.documentElement.classList.remove('light')
      document.documentElement.classList.add('dark')
    }
    try {
      localStorage.setItem('apex-theme', newTheme)
    } catch {}
  }

  function handleSelect(newTheme: ThemeType) {
    setTheme(newTheme)
    applyTheme(newTheme)
    setIsOpen(false)
  }

  const currentThemeObj = THEMES.find((t) => t.id === theme) || THEMES[0]

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 rounded-lg border border-border bg-panel px-3 py-1.5 text-xs font-semibold text-foreground shadow-sm transition-colors hover:bg-accent focus:outline-none"
        aria-expanded={isOpen}
        aria-label="Select theme"
      >
        <span
          className={`h-3 w-3 rounded-full border ${currentThemeObj.swatch}`}
          aria-hidden="true"
        />
        <span className="hidden sm:inline">{currentThemeObj.name}</span>
        <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-popover p-2 shadow-xl backdrop-blur-lg z-50 animate-in fade-in zoom-in-95 duration-100">
          <div className="px-2 py-1 text-[10px] font-mono font-bold uppercase tracking-wider text-muted-foreground">
            Aesthetic Themes
          </div>
          <div className="mt-1 space-y-1">
            {THEMES.map((t) => {
              const active = t.id === theme
              return (
                <button
                  key={t.id}
                  onClick={() => handleSelect(t.id)}
                  className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs font-medium transition-colors ${
                    active
                      ? 'bg-accent text-accent-foreground font-semibold'
                      : 'text-foreground hover:bg-accent/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`h-3.5 w-3.5 rounded-full border ${t.swatch}`} />
                    <span>{t.name}</span>
                  </div>
                  {active && <Check className="h-3.5 w-3.5 text-primary" />}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
