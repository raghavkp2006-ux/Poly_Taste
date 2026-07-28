import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui"
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

// ── Helpers ─────────────────────────────────────────────────────────

const actionIcons: Record<ActivityAction, React.ElementType> = {
  rated: Star,
  liked: Heart,
  viewed: Eye,
  added: PlusCircle,
}

const actionColors: Record<ActivityAction, string> = {
  rated: "text-amber-500 bg-amber-500/10",
  liked: "text-rose-500 bg-rose-500/10",
  viewed: "text-blue-500 bg-blue-500/10",
  added: "text-emerald-500 bg-emerald-500/10",
}

const categoryIcons: Record<Category, React.ElementType> = {
  anime: Tv,
  restaurant: UtensilsCrossed,
  music: Music,
}

function timeAgo(isoDate: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(isoDate).getTime()) / 1000
  )
  if (seconds < 60) return "just now"
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function describeAction(item: ActivityItem): string {
  switch (item.action) {
    case "rated":
      return `You rated ${item.itemTitle} ${item.detail} star${item.detail !== "1" ? "s" : ""}`
    case "liked":
      return `You liked ${item.itemTitle}`
    case "viewed":
      return `You viewed ${item.itemTitle}`
    case "added":
      return `You added ${item.itemTitle} to your list`
  }
}

// ── Component ───────────────────────────────────────────────────────

interface ActivityFeedProps {
  items: ActivityItem[]
  loading: boolean
}

export function ActivityFeed({ items, loading }: ActivityFeedProps) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2.5">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-pink-500 to-rose-500">
          <Activity className="h-4 w-4 text-white" />
        </div>
        <h2 className="text-base font-semibold">Latest activity</h2>
      </div>

      <div className="rounded-xl border border-border bg-card/50 divide-y divide-border overflow-hidden">
        {loading ? (
          <div className="space-y-0">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3">
                <Skeleton className="h-8 w-8 rounded-full shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-2.5 w-1/4" />
                </div>
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No activity yet — start exploring!
            </p>
          </div>
        ) : (
          items.slice(0, 10).map((item, i) => (
            <ActivityRow key={item.id} item={item} index={i} />
          ))
        )}
      </div>
    </section>
  )
}

// ── Row ──────────────────────────────────────────────────────────────

function ActivityRow({ item, index }: { item: ActivityItem; index: number }) {
  const ActionIcon = actionIcons[item.action]
  const CategoryIcon = categoryIcons[item.category]
  const colorClass = actionColors[item.action]

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04, duration: 0.25 }}
      className="flex items-center gap-3 px-4 py-3 hover:bg-muted/40 transition-colors cursor-default"
    >
      {/* Action icon */}
      <div
        className={cn(
          "flex items-center justify-center w-8 h-8 rounded-full shrink-0",
          colorClass
        )}
      >
        <ActionIcon className="h-4 w-4" />
      </div>

      {/* Description */}
      <div className="flex-1 min-w-0">
        <p className="text-sm leading-snug truncate">
          {describeAction(item)}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          <CategoryIcon className="h-3 w-3 text-muted-foreground" />
          <span className="text-[10px] text-muted-foreground capitalize">
            {item.category}
          </span>
          <span className="text-[10px] text-muted-foreground">·</span>
          <span className="text-[10px] text-muted-foreground">
            {timeAgo(item.timestamp)}
          </span>
        </div>
      </div>
    </motion.div>
  )
}
