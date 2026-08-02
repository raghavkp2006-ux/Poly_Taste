"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export interface HeroAction {
  label: string
  href: string
  variant?: "default" | "secondary" | "outline" | "ghost"
  className?: string
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void
  /** Domain accent color for the glow — overrides variant style */
  accentColor?: string
}

export interface HeroProps extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  title: React.ReactNode
  subtitle?: React.ReactNode
  actions?: HeroAction[]
  titleClassName?: string
  subtitleClassName?: string
  actionsClassName?: string
}

const Hero = React.forwardRef<HTMLElement, HeroProps>(
  (
    {
      className,
      title,
      subtitle,
      actions,
      titleClassName,
      subtitleClassName,
      actionsClassName,
      ...props
    },
    ref,
  ) => {
    return (
      <section
        ref={ref}
        className={cn("relative py-10 md:py-14 text-center", className)}
        {...props}
      >
        <motion.div
          initial={{ y: 24, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ ease: [0.22, 1, 0.36, 1], duration: 0.7 }}
          className="flex flex-col items-center gap-5"
        >
          {/* Domain pills */}
          <div className="flex items-center gap-2">
            <DomainPill label="Music"  color="#7C6CF0" />
            <span className="text-muted-foreground text-xs font-mono">·</span>
            <DomainPill label="Anime"  color="#FF7A59" />
            <span className="text-muted-foreground text-xs font-mono">·</span>
            <DomainPill label="Food"   color="#E3A857" />
          </div>

          {/* Title */}
          <h1
            className={cn(
              "text-4xl sm:text-5xl md:text-6xl font-display font-bold tracking-tight text-foreground",
              titleClassName,
            )}
          >
            {title}
          </h1>

          {/* Subtitle */}
          {subtitle && (
            <p
              className={cn(
                "text-base md:text-lg text-muted-foreground font-sans max-w-[560px] leading-relaxed",
                subtitleClassName,
              )}
            >
              {subtitle}
            </p>
          )}

          {/* Action buttons */}
          {actions && actions.length > 0 && (
            <div className={cn("flex flex-wrap gap-3 justify-center", actionsClassName)}>
              {actions.map((action, index) => (
                <DomainButton key={index} action={action} />
              ))}
            </div>
          )}
        </motion.div>
      </section>
    )
  },
)
Hero.displayName = "Hero"

export { Hero }

// ── Domain pill ───────────────────────────────────────────────────────

function DomainPill({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="text-[10px] font-mono uppercase tracking-widest px-2.5 py-0.5 rounded-full"
      style={{
        color,
        backgroundColor: `${color}15`,
        border: `1px solid ${color}30`,
      }}
    >
      {label}
    </span>
  )
}

// ── Domain-accented action button ─────────────────────────────────────

function DomainButton({ action }: { action: HeroAction }) {
  const { accentColor, className, onClick, href, label, variant = "outline" } = action

  const accentStyle = accentColor
    ? {
        border: `1px solid ${accentColor}40`,
        color: accentColor,
        backgroundColor: `${accentColor}12`,
        boxShadow: `0 0 20px ${accentColor}20`,
      }
    : undefined

  return (
    <Button
      variant={variant}
      className={cn(
        "relative overflow-hidden font-sans font-medium transition-all duration-200",
        "hover:scale-[1.02] active:scale-[0.97]",
        className,
      )}
      style={accentStyle}
      asChild
    >
      <a
        href={href}
        onClick={onClick}
        style={accentStyle}
        className={cn(
          "inline-flex items-center gap-2",
          "hover:brightness-110",
        )}
      >
        {label}
      </a>
    </Button>
  )
}
