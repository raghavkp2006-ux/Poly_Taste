/**
 * ConvergenceHalo — the signature moment for Poly_Taste.
 *
 * Three domain glows (music indigo, anime coral, food copper-gold) drift
 * from their starting positions and converge into a single violet→cyan ring
 * behind frosted glass. This is the only place in the app where all three
 * accents appear simultaneously.
 *
 * Motion: animated by default. Respects prefers-reduced-motion — falls back
 * to the static composed state when motion is disabled.
 */
import { useEffect, useRef, useState } from "react"

// ── Reduced-motion hook ───────────────────────────────────────────────

function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === "undefined") return false
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches
  })

  useEffect(() => {
    const mq      = window.matchMedia("(prefers-reduced-motion: reduce)")
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
    mq.addEventListener("change", handler)
    return () => mq.removeEventListener("change", handler)
  }, [])

  return reduced
}

// ── Types ─────────────────────────────────────────────────────────────

interface GlobeState {
  music: { x: number; y: number; opacity: number }
  anime: { x: number; y: number; opacity: number }
  food:  { x: number; y: number; opacity: number }
}

const CONVERGED: GlobeState = {
  music: { x: 0,   y: 0,   opacity: 1 },
  anime: { x: 0,   y: 0,   opacity: 1 },
  food:  { x: 0,   y: 0,   opacity: 1 },
}

const DRIFTING: GlobeState = {
  music: { x: -28, y: -20, opacity: 0.65 },
  anime: { x:  28, y: -20, opacity: 0.65 },
  food:  { x:   0, y:  32, opacity: 0.65 },
}

// ── Component ─────────────────────────────────────────────────────────

export function ConvergenceHalo({ score }: { score?: number }) {
  const reduced = useReducedMotion()
  const [phase, setPhase] = useState<"drifting" | "converging" | "converged">("drifting")
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Animate through phases (drift → converge → drift) every 8 seconds
  useEffect(() => {
    if (reduced) {
      setPhase("converged")
      return
    }

    function cycle() {
      setPhase("drifting")
      timerRef.current = setTimeout(() => {
        setPhase("converging")
        timerRef.current = setTimeout(() => {
          setPhase("converged")
          timerRef.current = setTimeout(() => {
            cycle()
          }, 4000)
        }, 2000)
      }, 3000)
    }

    cycle()
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [reduced])

  const glows: GlobeState = phase === "drifting" ? DRIFTING : CONVERGED

  const TRANSITION = reduced
    ? "none"
    : "transform 2s cubic-bezier(0.22, 1, 0.36, 1), opacity 2s ease"

  const ringOpacity = phase === "converged" ? 1 : 0

  return (
    <div
      className="relative flex flex-col items-center gap-6 py-8"
      aria-label="Taste Convergence — where music, anime, and food intersect"
    >
      {/* Label */}
      <div className="text-center space-y-1">
        <p
          className="text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground"
        >
          Convergence
        </p>
        <p className="text-sm font-sans text-muted-foreground">
          Where your signals unite.
        </p>
      </div>

      {/* Halo container */}
      <div
        className="relative"
        style={{ width: 160, height: 160 }}
      >
        {/* Frosted glass disc */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: "rgba(18,24,31,0.5)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        />

        {/* Music glow — indigo */}
        <GlowOrb
          color="#7C6CF0"
          state={glows.music}
          transition={TRANSITION}
          size={80}
        />
        {/* Anime glow — coral */}
        <GlowOrb
          color="#FF7A59"
          state={glows.anime}
          transition={TRANSITION}
          size={80}
        />
        {/* Food glow — copper-gold */}
        <GlowOrb
          color="#E3A857"
          state={glows.food}
          transition={TRANSITION}
          size={76}
        />

        {/* Convergence ring — the signature violet→cyan arc */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            opacity: ringOpacity,
            transition: reduced ? "none" : "opacity 1.5s ease",
          }}
        >
          {/* Outer glow ring */}
          <div
            className="absolute inset-[-4px] rounded-full"
            style={{
              background: "transparent",
              border: "2px solid transparent",
              backgroundClip: "padding-box",
              boxShadow: "0 0 20px #7C6CF080, 0 0 40px #3ED6C440",
            }}
          />
          {/* SVG gradient ring */}
          <svg
            className="absolute inset-0"
            viewBox="0 0 160 160"
            style={{
              animation: reduced ? "none" : "halo-spin 12s linear infinite",
            }}
          >
            <defs>
              <linearGradient id="halo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%"   stopColor="#7C6CF0" />
                <stop offset="50%"  stopColor="#5B8BF0" />
                <stop offset="100%" stopColor="#3ED6C4" />
              </linearGradient>
            </defs>
            <circle
              cx="80"
              cy="80"
              r="74"
              fill="none"
              stroke="url(#halo-grad)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeDasharray="120 360"
              style={{ filter: "drop-shadow(0 0 6px #7C6CF0)" }}
            />
          </svg>
          {/* Center mark / Score */}
          <div
            className="absolute inset-0 flex flex-col items-center justify-center transition-opacity duration-1000"
            style={{ opacity: phase === "converged" ? 1 : 0 }}
          >
            {score !== undefined ? (
              <div className="flex flex-col items-center">
                <span className="text-3xl font-display font-bold bg-clip-text text-transparent bg-gradient-to-br from-[#7C6CF0] to-[#3ED6C4]">
                  {score}
                </span>
                <span className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground mt-0.5">
                  Match
                </span>
              </div>
            ) : (
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  background: "linear-gradient(135deg, #7C6CF0, #3ED6C4)",
                  boxShadow: "0 0 12px #7C6CF0, 0 0 24px #3ED6C440",
                }}
              />
            )}
          </div>
        </div>

        {/* Domain labels — shown when converged */}
        <DomainLabels visible={phase === "converged"} reduced={reduced} />
      </div>

      {/* Domain legend */}
      <div className="flex items-center gap-5 text-[10px] font-mono uppercase tracking-widest">
        <LegendItem color="#7C6CF0" label="Music" />
        <LegendItem color="#FF7A59" label="Anime" />
        <LegendItem color="#E3A857" label="Food"  />
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────

function GlowOrb({
  color,
  state,
  transition,
  size,
}: {
  color: string
  state: { x: number; y: number; opacity: number }
  transition: string
  size: number
}) {
  return (
    <div
      className="absolute rounded-full"
      style={{
        width:  size,
        height: size,
        top:    `calc(50% - ${size / 2}px)`,
        left:   `calc(50% - ${size / 2}px)`,
        background: `radial-gradient(circle, ${color}50 0%, ${color}00 70%)`,
        filter: `blur(16px)`,
        transform: `translate(${state.x}px, ${state.y}px)`,
        opacity:   state.opacity,
        transition,
      }}
    />
  )
}

function DomainLabels({
  visible,
  reduced,
}: {
  visible: boolean
  reduced: boolean
}) {
  const items = [
    { label: "♪", color: "#7C6CF0", x: -46, y: -46 },
    { label: "◈", color: "#FF7A59", x:  46, y: -46 },
    { label: "✦", color: "#E3A857", x:   0, y:  52 },
  ]

  return (
    <>
      {items.map((item) => (
        <div
          key={item.label}
          className="absolute"
          style={{
            top:    "50%",
            left:   "50%",
            transform: `translate(calc(-50% + ${item.x}px), calc(-50% + ${item.y}px))`,
            opacity: visible ? 1 : 0,
            transition: reduced ? "none" : "opacity 0.8s ease 0.5s",
            fontSize: 11,
            fontFamily: "JetBrains Mono, monospace",
            color: item.color,
            textShadow: `0 0 8px ${item.color}`,
          }}
        >
          {item.label}
        </div>
      ))}
    </>
  )
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color, boxShadow: `0 0 4px ${color}` }}
      />
      <span style={{ color }}>{label}</span>
    </div>
  )
}
