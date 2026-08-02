/**
 * components/ui.tsx — Canonical UI primitives for Poly_Taste
 *
 * Button is re-exported from ./ui/button (cva + Radix Slot) so all
 * consumers (AnimeDetail, AnimeGrid, ActivityFeed, ContinueRow, TopBar)
 * share the same implementation as hero.tsx which imports from ./ui/button.
 */
import * as React from "react"
import { cn } from "@/lib/utils"

// ── Re-export canonical Button ───────────────────────────────────────
export { Button, buttonVariants } from "./ui/button"
export type { ButtonProps } from "./ui/button"

// ── Input ────────────────────────────────────────────────────────────

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-lg",
        "border border-border bg-[rgba(18,24,31,0.8)]",
        "px-3 py-2 text-sm text-foreground font-sans",
        "placeholder:text-muted-foreground",
        "backdrop-blur-sm",
        "transition-colors duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "file:border-0 file:bg-transparent file:text-sm file:font-medium",
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Input.displayName = "Input"

// ── Card (glass-card variant) ─────────────────────────────────────────

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "glass-card text-card-foreground",
        "overflow-hidden",
        className
      )}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 p-5", className)}
      {...props}
    />
  )
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("font-display font-semibold leading-none tracking-tight text-foreground", className)}
      {...props}
    />
  )
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-5 pt-0", className)} {...props} />
  )
}

// ── Tabs ──────────────────────────────────────────────────────────────

export function Tabs({ defaultValue, children }: any) {
  const [active, setActive] = React.useState(defaultValue)
  return (
    <div className="w-full">
      {React.Children.map(children, (child) => {
        if (child.type === TabsList) return React.cloneElement(child, { active, setActive })
        if (child.type === TabsContent) return child.props.value === active ? child : null
        return child
      })}
    </div>
  )
}

export function TabsList({ active, setActive, children, className }: any) {
  return (
    <div
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-lg",
        "bg-white/[0.04] border border-white/[0.06]",
        "p-1 text-muted-foreground",
        className
      )}
    >
      {React.Children.map(children, (child) =>
        React.cloneElement(child, { active, setActive })
      )}
    </div>
  )
}

export function TabsTrigger({ value, active, setActive, children, className }: any) {
  const isActive = active === value
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5",
        "text-sm font-sans font-medium",
        "ring-offset-background transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-white/10 text-foreground shadow-sm border border-white/10"
          : "hover:text-foreground",
        className
      )}
      onClick={() => setActive(value)}
    >
      {children}
    </button>
  )
}

export function TabsContent({ children, className }: any) {
  return (
    <div
      className={cn(
        "mt-2 ring-offset-background",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
    >
      {children}
    </div>
  )
}

// ── Switch ───────────────────────────────────────────────────────────

export function Switch({ checked, onCheckedChange }: any) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full",
        "border-2 border-transparent",
        "transition-colors duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "disabled:cursor-not-allowed disabled:opacity-50",
        checked ? "bg-[#7C6CF0]" : "bg-white/10"
      )}
    >
      <span
        className={cn(
          "pointer-events-none block h-4 w-4 rounded-full",
          "bg-white shadow-lg ring-0 transition-transform duration-200",
          checked ? "translate-x-4" : "translate-x-0"
        )}
      />
    </button>
  )
}

// ── Skeleton ─────────────────────────────────────────────────────────

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-lg bg-white/[0.06]", className)}
      {...props}
    />
  )
}

// ── Badge ─────────────────────────────────────────────────────────────

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "success" | "music" | "anime" | "food"
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-sans font-semibold transition-colors",
        variant === "default"   && "bg-[#7C6CF0]/20 text-[#7C6CF0] border border-[#7C6CF0]/30",
        variant === "secondary" && "bg-white/5 text-muted-foreground border border-white/10",
        variant === "outline"   && "border border-border text-foreground",
        variant === "success"   && "bg-emerald-400/10 text-emerald-400 border border-emerald-400/20",
        variant === "music"     && "bg-[#7C6CF0]/15 text-[#7C6CF0] border border-[#7C6CF0]/25",
        variant === "anime"     && "bg-[#FF7A59]/15 text-[#FF7A59] border border-[#FF7A59]/25",
        variant === "food"      && "bg-[#E3A857]/15 text-[#E3A857] border border-[#E3A857]/25",
        className
      )}
      {...props}
    />
  )
}

// ── Avatar ────────────────────────────────────────────────────────────

export function Avatar({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative flex h-9 w-9 shrink-0 overflow-hidden rounded-full",
        "bg-[#12181F] border border-white/10",
        className
      )}
      {...props}
    />
  )
}

export function AvatarFallback({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "flex h-full w-full items-center justify-center rounded-full",
        "bg-gradient-to-br from-[#7C6CF0]/80 to-[#3ED6C4]/80",
        "text-white text-sm font-display font-semibold",
        className
      )}
      {...props}
    />
  )
}

// ── ScrollArea (horizontal snap) ──────────────────────────────────────

export function ScrollArea({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex overflow-x-auto scrollbar-hide scroll-smooth snap-x snap-mandatory gap-4 pb-2",
        className
      )}
      {...props}
    />
  )
}

// ── Tooltip (CSS-only) ────────────────────────────────────────────────

interface TooltipProps extends React.HTMLAttributes<HTMLDivElement> {
  content: string
}

export function Tooltip({ content, children, className, ...props }: TooltipProps) {
  return (
    <div className={cn("group/tooltip relative inline-flex", className)} {...props}>
      {children}
      <span
        className={cn(
          "pointer-events-none absolute left-1/2 -translate-x-1/2 -top-9 z-50",
          "whitespace-nowrap rounded-lg px-2.5 py-1.5",
          "glass-panel text-xs text-foreground",
          "opacity-0 transition-opacity duration-150",
          "group-hover/tooltip:opacity-100"
        )}
      >
        {content}
      </span>
    </div>
  )
}
