import type { Domain } from "../../tokens"
import { domainColor, domainAlpha, fontFamily } from "../../tokens"

interface ConnectionBadgeProps {
  /** True if the service is connected */
  connected: boolean
  /** Which content domain this badge represents */
  domain: Domain
  /** Outer diameter in px (default 14) */
  size?: number
  /** Optional letter to display inside the ring (e.g. 'S' or 'A') */
  letter?: string
  /** Optional className for the wrapper */
  className?: string
}

export function ConnectionBadge({
  connected,
  domain,
  size = 14,
  letter,
  className = "",
}: ConnectionBadgeProps) {
  const accent = domainColor[domain]
  const strokeW = Math.max(1.5, size * 0.12)
  const r = (size - strokeW) / 2
  const circ = 2 * Math.PI * r

  return (
    <div
      className={`relative flex items-center justify-center shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: "rotate(-90deg)" }}
        className="absolute inset-0"
      >
        {/* Track ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="currentColor"
          className="text-black/[0.08] dark:text-white/[0.12]"
          strokeWidth={strokeW}
        />
        {/* Connected progress ring */}
        {connected && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={accent}
            strokeWidth={strokeW}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={0}
            style={{
              filter: `drop-shadow(0 0 3px ${domainAlpha(domain, 0.5)})`,
              transition: "stroke-dashoffset 0.5s ease-in-out",
            }}
          />
        )}
      </svg>
      {letter && (
        <span
          className={connected ? "" : "text-[#71717A] dark:text-[#A1A1AA]"}
          style={{
            fontSize: size * 0.45,
            fontFamily: fontFamily.mono,
            fontWeight: 700,
            color: connected ? accent : undefined,
            lineHeight: 1,
            position: "relative",
            zIndex: 10,
          }}
        >
          {letter}
        </span>
      )}
    </div>
  )
}
