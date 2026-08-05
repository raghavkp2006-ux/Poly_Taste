/**
 * StationBadge — circular score/match-% badge with a colored ring.
 *
 * Domain-coded ring color, mono numerals inside.
 * Drop-in replacement for any existing score stamp styling.
 */

import type { Domain } from "../../tokens"
import { domainColor, domainAlpha, fontFamily, inkAlpha } from "../../tokens"

interface StationBadgeProps {
  /** Numeric value to display (0–100 score, match %, etc.) */
  value: number
  /** Which content domain determines the ring color */
  domain: Domain
  /** Outer diameter in px (default 44) */
  size?: number
  /** Optional className for the wrapper */
  className?: string
}

export function StationBadge({
  value,
  domain,
  size = 44,
  className = "",
}: StationBadgeProps) {
  const accent   = domainColor[domain]
  const r        = (size - 6) / 2
  const circ     = 2 * Math.PI * r
  const progress = Math.min(Math.max(value, 0), 100)
  const offset   = circ * (1 - progress / 100)

  return (
    <div
      className={`relative ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: "rotate(-90deg)" }}
      >
        {/* Track ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={inkAlpha(0.08)}
          strokeWidth={3}
        />
        {/* Progress ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={accent}
          strokeWidth={3}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{
            filter: `drop-shadow(0 0 4px ${domainAlpha(domain, 0.5)})`,
            transition: "stroke-dashoffset 0.8s cubic-bezier(0.22, 1, 0.36, 1)",
          }}
        />
      </svg>
      {/* Numeral label */}
      <div
        className="absolute inset-0 flex items-center justify-center"
        style={{
          fontSize:   size * 0.24,
          fontFamily: fontFamily.mono,
          fontWeight: 700,
          color:      accent,
          lineHeight: 1,
        }}
      >
        {Math.round(value)}
      </div>
    </div>
  )
}
