'use client'

import { useState, useRef, useEffect } from 'react'
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  FileText,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

export function VoiceBriefingPlayer() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [duration, setDuration] = useState(30)
  const [currentTime, setCurrentTime] = useState(0)
  const [showTranscript, setShowTranscript] = useState(false)
  const [playbackRate, setPlaybackRate] = useState<number>(1.0)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setDuration(Math.floor(audio.duration))
      }
    }

    const handleTimeUpdate = () => {
      setCurrentTime(Math.floor(audio.currentTime))
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
    }

    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [])

  const togglePlay = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      audio.play().then(() => {
        setIsPlaying(true)
      }).catch((err) => {
        console.error('Audio playback error:', err)
      })
    }
  }

  const toggleMute = () => {
    const audio = audioRef.current
    if (!audio) return
    audio.muted = !isMuted
    setIsMuted(!isMuted)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current
    if (!audio) return
    const newTime = Number(e.target.value)
    audio.currentTime = newTime
    setCurrentTime(newTime)
  }

  const cyclePlaybackRate = () => {
    const audio = audioRef.current
    if (!audio) return
    const rates = [1.0, 1.25, 1.5]
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length
    const nextRate = rates[nextIdx]
    audio.playbackRate = nextRate
    setPlaybackRate(nextRate)
  }

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-2">
      {/* Hidden HTML5 Audio Element */}
      <audio
        ref={audioRef}
        src="/audio/apex_executive_briefing.wav"
        preload="metadata"
      />

      {/* Main Player Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/30 bg-panel/95 p-3 sm:px-4 sm:py-2.5 shadow-lg backdrop-blur hover-glow transition-all">
        {/* Play/Pause Button & Branding */}
        <div className="flex items-center gap-3">
          <button
            onClick={togglePlay}
            className={`flex h-9 w-9 items-center justify-center rounded-full transition-all shadow-md ${isPlaying
              ? 'bg-primary text-primary-foreground scale-105'
              : 'bg-primary/20 text-primary hover:bg-primary hover:text-primary-foreground'
              }`}
            aria-label={isPlaying ? 'Pause Audio Briefing' : 'Play Audio Briefing'}
            title={isPlaying ? 'Pause' : 'Listen to 60s Briefing'}
          >
            {isPlaying ? <Pause className="h-4 w-4 fill-current" /> : <Play className="h-4 w-4 fill-current ml-0.5" />}
          </button>

          <div className="text-left space-y-0.5">
            <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-foreground">
              <span>30s Executive Audio Brief</span>
              <span className="rounded bg-primary/15 px-1.5 py-0.5 font-mono text-[9px] font-extrabold text-primary border border-primary/30 shadow-xs">
                Sarvam AI (Advait)
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground hidden sm:block">
              Indic AI Voice Walkthrough for Razorpay AI Buildathon
            </p>
          </div>
        </div>

        {/* Dynamic Waveform Visualizer */}
        <div className="hidden md:flex items-center gap-0.5 h-5 px-2">
          {[40, 75, 50, 90, 60, 100, 45, 80, 55, 70].map((h, i) => (
            <span
              key={i}
              className={`w-0.5 rounded-full bg-primary transition-all duration-150 ${isPlaying ? 'animate-pulse' : 'opacity-30'
                }`}
              style={{
                height: isPlaying ? `${Math.max(20, (h * (i % 2 === 0 ? 0.9 : 1.1))) % 100}%` : '20%',
                animationDelay: `${i * 75}ms`,
              }}
            />
          ))}
        </div>

        {/* Progress & Quick Controls */}
        <div className="flex items-center gap-2.5 font-mono text-xs ml-auto">
          <span className="text-muted-foreground text-[11px] min-w-[65px] text-right">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          <button
            onClick={cyclePlaybackRate}
            className="rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-bold text-muted-foreground hover:text-foreground"
            title="Toggle playback speed"
          >
            {playbackRate}x
          </button>

          <button
            onClick={toggleMute}
            className="text-muted-foreground hover:text-foreground p-1"
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <VolumeX className="h-3.5 w-3.5 text-danger" /> : <Volume2 className="h-3.5 w-3.5" />}
          </button>

          <button
            onClick={() => setShowTranscript(!showTranscript)}
            className={`flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-semibold border transition-all ${showTranscript
              ? 'bg-accent text-foreground border-primary/40'
              : 'border-border bg-background text-muted-foreground hover:text-foreground'
              }`}
            title="Show spoken transcript"
          >
            <FileText className="h-3 w-3" />
            <span className="hidden sm:inline">Script</span>
            {showTranscript ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* Progress Slider Track */}
      <div className="px-1">
        <input
          type="range"
          min="0"
          max={duration || 30}
          value={currentTime}
          onChange={handleSeek}
          className="w-full h-1 bg-border rounded-lg appearance-none cursor-pointer accent-primary focus:outline-none"
        />
      </div>

      {/* Expandable Spoken Transcript Drawer */}
      {showTranscript && (
        <div className="rounded-xl border border-border bg-panel p-4 text-xs font-mono space-y-2 animate-fade-up text-left shadow-md">
          <div className="flex items-center justify-between border-b border-border pb-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
            <span className="flex items-center gap-1 font-bold text-primary">
              <Sparkles className="h-3 w-3" /> Spoken Script (Sarvam Indic Voice)
            </span>
            <span>Language: English (en-IN) · Speaker: Advait (Studio Pro) · Pace: 1.0x</span>
          </div>
          <p className="text-foreground/90 leading-relaxed font-sans text-xs">
            &ldquo;Welcome to APEX Capital and Assurance, built for the Razorpay AI Buildathon 2026. Today, autonomous AI buyer agents can transact instantly. But they settle blindly. Traditional payment rails disburse funds before verifying if delivery occurred or if seller GSTIN is legitimate. APEX solves this. We gate Razorpay Route pre-settlement behind cryptographic delivery proofs, Horowitz–Sahni meet-in-the-middle subset-sum matching, and statutory GSTIN Mod-36 checksums, ensuring 0 false matches on tested fixtures and zero float rounding errors. Once verified, APEX converts merchant revenue into instant working capital, and automatically recovers advances through a twelve percent nodal settlement sweep at the source. Click Launch Console to explore the live autonomous settlement radar.&rdquo;
          </p>
        </div>
      )}
    </div>
  )
}
