/**
 * Card — parchment surface, ink text, subtle shadow.
 *
 * The base recommendation-card shell for the Interchange system.
 * Wraps children in a warm paper surface with consistent padding,
 * border-radius, and shadow. Accepts an optional domain prop to
 * add a top-edge accent line.
 */

import type { Domain } from "../../tokens"
import { CARD_SURFACE, domainColor, domainAlpha, fontFamily } from "../../tokens"

interface CardProps {
  children: React.ReactNode
  /** If provided, renders a thin accent bar along the top edge */
  domain?: Domain
  /** Optional className for the outer wrapper */
  className?: string
  /** Optional inline style override */
  style?: React.CSSProperties
  /** Click handler */
  onClick?: () => void
}

export function Card({
  children,
  domain,
  className = "",
  style,
  onClick,
}: CardProps) {
  return (
    <div
      className={`overflow-hidden transition-all duration-300 ${
        onClick ? "cursor-pointer hover:shadow-lg" : ""
      } ${className}`}
      style={{
        ...CARD_SURFACE,
        fontFamily: fontFamily.body,
        ...style,
      }}
      onClick={onClick}
    >
      {/* Domain accent bar */}
      {domain && (
        <div
          style={{
            height:     2,
            background: `linear-gradient(90deg, ${domainColor[domain]} 0%, ${domainAlpha(domain, 0)} 80%)`,
          }}
        />
      )}
      {children}
    </div>
  )
}
