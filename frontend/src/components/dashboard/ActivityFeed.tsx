import {
  Star,
  Heart,
  Eye,
  PlusCircle,
  Tv,
  UtensilsCrossed,
  Music,
  Activity,
} from "lucide-react"
import { motion } from "framer-motion"
import type { ActivityItem, ActivityAction, Category } from "../../types"

// ── Action icons & accent colors ─────────────────────────────────────

const ACTION_ICONS: Record<ActivityAction, React.ElementType> = {
  rated:  Star,
  liked:  Heart,
  viewed: Eye,
  added:  PlusCircle,
}

const ACTION_COLORS: Record<ActivityAction, string> = {
  rated:  "#E3A857",
  liked:  "#FF7A59",
  viewed: "#7C6CF0",
  added:  "#3ED6C4",
}

const CATEGORY_ICONS: Record<Category, React.ElementType> = {
  anime:      Tv,
  restaurant: UtensilsCrossed,
  music:      Music,
}

const CATEGORY_COLORS: Record<Category, string> = {
  anime:      "#FF7A59",
  restaurant: "#E3A857",
  music:      "#7C6CF0",
}

// ── Helpers ───────────────────────────────────────────────────────────

function timeAgo(isoDate: string): string {
  const seconds = Math.floor((Date.now() - new Date(isoDate).getTime()) / 1000)
  if (seconds < 60)  return "just now"
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60)  return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24)    return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function describeAction(item: ActivityItem): string {
  switch (item.action) {
    case "rated":  return `Rated ${item.itemTitle} ${item.detail} star${item.detail !== "1" ? "s" : ""}`
    case "liked":  return `Liked ${item.itemTitle}`
    case "viewed": return `Viewed ${item.itemTitle}`
    case "added":  return `Added ${item.itemTitle} to list`
  }
}

// ── Component ─────────────────────────────────────────────────────────

interface ActivityFeedProps {
  items: ActivityItem[]
  loading: boolean
}

export function ActivityFeed({ items, loading }: ActivityFeedProps) {
  return (
    <section className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <div
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: "#3ED6C4", boxShadow: "0 0 6px #3ED6C4" }}
        />
        <h2 className="text-sm font-display font-semibold tracking-wide uppercase text-foreground">
          Activity
        </h2>
        <Activity className="h-4 w-4 text-muted-foreground opacity-60" />
      </div>

      {loading ? (
        <div className="flex gap-3 overflow-hidden">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="w-[200px] shrink-0 rounded-xl overflow-hidden"
              style={{
                background: "rgba(18,24,31,0.6)",
                border: "1px solid rgba(255,255,255,0.05)",
              }}
            >
              <div className="h-20 skeleton-dark rounded-none" />
              <div className="p-3 space-y-1.5">
                <div className="h-2 w-3/4 rounded-full skeleton-dark" />
                <div className="h-2 w-1/2 rounded-full skeleton-dark" />
              </div>
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div
          className="rounded-xl border border-dashed px-4 py-5 text-center"
          style={{ borderColor: "rgba(255,255,255,0.1)" }}
        >
          <p className="text-sm font-sans text-muted-foreground">
            No activity yet — start exploring to build your trail.
          </p>
        </div>
      ) : (
        <div className="flex gap-3 overflow-x-auto scrollbar-hide snap-x snap-mandatory pb-2">
          {items.map((item, i) => (
            <ActivityCard key={item.id} item={item} index={i} />
          ))}
        </div>
      )}
    </section>
  )
}

// ── Activity card ──────────────────────────────────────────────────────

const DOMAIN_GLOW: Record<Category, string> = {
  anime:      "glow-edge-anime",
  restaurant: "glow-edge-food",
  music:      "glow-edge-music",
}

function ActivityCard({ item, index }: { item: ActivityItem; index: number }) {
  const ActionIcon   = ACTION_ICONS[item.action]
  const CategoryIcon = CATEGORY_ICONS[item.category]
  const actionColor  = ACTION_COLORS[item.action]
  const catColor     = CATEGORY_COLORS[item.category]
  const glow         = DOMAIN_GLOW[item.category]

  return (
    <motion.div
      initial={{ opacity: 0, y: 14, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.05, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
      className="snap-start shrink-0 w-[200px] cursor-default group"
    >
      <div
        className={`relative overflow-hidden rounded-xl gradient-border ${glow} transition-all duration-300`}
        style={{
          background: "rgba(18,24,31,0.75)",
          backdropFilter: "blur(10px)",
        }}
      >
        {/* Domain accent glow behind content */}
        <div
          className="absolute top-0 left-0 w-full h-1"
          style={{
            background: `linear-gradient(90deg, ${catColor} 0%, transparent 80%)`,
            opacity: 0.6,
          }}
        />

        {/* Icon section (instead of image) */}
        <div className="relative h-20 overflow-hidden flex items-center justify-center">
          <div
            className="absolute inset-0"
            style={{ backgroundColor: `${actionColor}12` }}
          />
          <ActionIcon className="h-8 w-8 relative z-10" style={{ color: actionColor, opacity: 0.8 }} />
          {/* Scrim */}
          <div
            className="absolute inset-0 z-20"
            style={{ background: "linear-gradient(to top, rgba(18,24,31,0.85) 0%, transparent 80%)" }}
          />
        </div>

        <div className="p-3 space-y-1.5">
          <h3 className="text-xs font-sans font-semibold leading-snug line-clamp-2 text-foreground">
            {describeAction(item)}
          </h3>
          <div className="flex items-center gap-1.5 mt-1">
            <CategoryIcon className="h-3 w-3" style={{ color: catColor }} />
            <span className="text-[10px] text-muted-foreground font-mono">
              {timeAgo(item.timestamp)}
            </span>
          </div>
        </div>

        {/* Spacer to match RecommendationRow height feel */}
        <div className="h-2" />
      </div>
    </motion.div>
  )
}
