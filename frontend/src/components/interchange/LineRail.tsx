/**
 * LineRail — a 3px colored vertical rail, domain-coded.
 *
 * Place on the left edge of any row belonging to a single domain.
 * Height fills parent by default; override with className or style.
 */

import type { Domain } from "../../tokens"
import { domainColor, domainAlpha } from "../../tokens"

interface LineRailProps {
  /** Which content domain this rail represents */
  domain: Domain
  /** Optional className override */
  className?: string
  /** Optional inline style override */
  style?: React.CSSProperties
}

export function LineRail({ domain, className = "", style }: LineRailProps) {
  const accent = domainColor[domain]
  return (
    <div
      className={`shrink-0 ${className}`}
      style={{
        width:           3,
        borderRadius:    1.5,
        backgroundColor: accent,
        boxShadow:       `0 0 6px ${domainAlpha(domain, 0.4)}`,
        alignSelf:       "stretch",
        ...style,
      }}
    />
  )
}
