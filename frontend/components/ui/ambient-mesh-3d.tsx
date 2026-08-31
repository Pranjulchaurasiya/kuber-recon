'use client'

import { useEffect, useRef } from 'react'

interface Point3D {
  x: number
  y: number
  z: number
  baseX: number
  baseY: number
  baseZ: number
  color: string
}

export function AmbientMesh3D() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    let width = (canvas.width = window.innerWidth)
    let height = (canvas.height = window.innerHeight)

    const handleResize = () => {
      if (!canvas) return
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
    }

    window.addEventListener('resize', handleResize)

    // Construct 3D Grid Points representing the Interconnected Multi-Rail Financial Ledger
    const cols = 22
    const rows = 14
    const spacingX = width > 1200 ? 90 : 60
    const spacingY = 75
    const points: Point3D[] = []

    const palette = ['#38bdf8', '#10b981', '#f59e0b', '#818cf8']

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = (c - cols / 2) * spacingX
        const y = (r - rows / 2) * spacingY + 120
        const z = Math.sin((c / cols) * Math.PI) * Math.cos((r / rows) * Math.PI) * 140
        const color = palette[(r + c) % palette.length]
        points.push({ x, y, z, baseX: x, baseY: y, baseZ: z, color })
      }
    }

    let angle = 0
    let mouseX = 0
    let mouseY = 0
    let targetMouseX = 0
    let targetMouseY = 0

    const handleMouseMove = (e: MouseEvent) => {
      targetMouseX = (e.clientX - width / 2) * 0.0004
      targetMouseY = (e.clientY - height / 2) * 0.0004
    }

    window.addEventListener('mousemove', handleMouseMove)

    // Render loop
    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Smooth mouse interpolation
      mouseX += (targetMouseX - mouseX) * 0.04
      mouseY += (targetMouseY - mouseY) * 0.04

      angle += 0.003

      // Perspective projection constants
      const fov = 480
      const cameraZ = 520

      // Update 3D coordinates with undulating harmonic wave
      const projected = points.map((p, idx) => {
        const row = Math.floor(idx / cols)
        const col = idx % cols

        // Undulating wave reflecting active financial stream
        const wave =
          Math.sin(angle * 1.5 + col * 0.35 + row * 0.25) * 45 +
          Math.cos(angle * 1.0 + col * 0.2) * 25

        const curX = p.baseX
        const curY = p.baseY + wave
        const curZ = p.baseZ

        // 3D Rotations (Pitch & Yaw influenced by mouse)
        const rotY_X = curX * Math.cos(mouseX) - curZ * Math.sin(mouseX)
        const rotY_Z = curX * Math.sin(mouseX) + curZ * Math.cos(mouseX)

        const rotX_Y = curY * Math.cos(0.45 + mouseY) - rotY_Z * Math.sin(0.45 + mouseY)
        const rotX_Z = curY * Math.sin(0.45 + mouseY) + rotY_Z * Math.cos(0.45 + mouseY)

        // 3D to 2D Screen Space Projection
        const zDist = rotX_Z + cameraZ
        const scale = zDist > 10 ? fov / zDist : 0
        const screenX = rotY_X * scale + width / 2
        const screenY = rotX_Y * scale + height / 2.3

        const alpha = Math.max(0.04, Math.min(0.65, (scale * 1.2) - 0.2))

        return { screenX, screenY, scale, alpha, color: p.color, z: zDist }
      })

      // Draw Grid Lines connecting nodes
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const idx = r * cols + c
          const p1 = projected[idx]

          // Connect Horizontal
          if (c < cols - 1) {
            const p2 = projected[idx + 1]
            ctx.beginPath()
            ctx.moveTo(p1.screenX, p1.screenY)
            ctx.lineTo(p2.screenX, p2.screenY)
            ctx.strokeStyle = `rgba(56, 189, 248, ${p1.alpha * 0.35})`
            ctx.lineWidth = Math.max(0.5, p1.scale * 0.7)
            ctx.stroke()
          }

          // Connect Vertical
          if (r < rows - 1) {
            const p2 = projected[idx + cols]
            ctx.beginPath()
            ctx.moveTo(p1.screenX, p1.screenY)
            ctx.lineTo(p2.screenX, p2.screenY)
            ctx.strokeStyle = `rgba(16, 185, 129, ${p1.alpha * 0.25})`
            ctx.lineWidth = Math.max(0.5, p1.scale * 0.7)
            ctx.stroke()
          }
        }
      }

      // Draw Sparkling Financial Data Nodes
      projected.forEach((p, idx) => {
        if (p.scale <= 0) return
        const radius = Math.max(1, p.scale * 2.2)

        ctx.beginPath()
        ctx.arc(p.screenX, p.screenY, radius, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.globalAlpha = p.alpha
        ctx.fill()

        // Glow on select active nodes
        if (idx % 7 === 0) {
          ctx.beginPath()
          ctx.arc(p.screenX, p.screenY, radius * 2.5, 0, Math.PI * 2)
          ctx.fillStyle = p.color
          ctx.globalAlpha = p.alpha * 0.3
          ctx.fill()
        }
      })

      ctx.globalAlpha = 1.0
      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('mousemove', handleMouseMove)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0 h-full w-full opacity-60 transition-opacity duration-1000"
      aria-hidden="true"
    />
  )
}
