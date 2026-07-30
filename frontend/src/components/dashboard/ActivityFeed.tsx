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

const actionIcons: Record<ActivityAction, React.ElementType> = {
  rated: Star,
  liked: Heart,
  viewed: Eye,
  added: PlusCircle,
}

const actionAccents: Record<ActivityAction, string> = {
  rated: "#E8A23D",
  liked: "#B23A2E",
  viewed: "#C6318C",
  added: "#4A9B8E",
}

const categoryIcons: Record<Category, React.ElementType> = {
  anime: Tv,
  restaurant: UtensilsCrossed,
  music: Music,
}

const categoryAccents: Record<Category, string> = {
  anime: "#E8A23D",
  restaurant: "#B23A2E",
  music: "#C6318C",
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

interface ActivityFeedProps {
  items: ActivityItem[]
  loading: boolean
}

export function ActivityFeed({ items, loading }: ActivityFeedProps) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2.5">
        <div
          className="flex items-center justify-center w-8 h-8 shrink-0"
          style={{ backgroundColor: "hsl(var(--sidebar-accent))" }}
        >
          <Activity className="h-4 w-4 text-parchment" />
        </div>
        <h2 className="text-base font-display tracking-wide uppercase text-foreground">
          Latest activity
        </h2>
      </div>

      <div
        className="rounded-none border border-border/40 overflow-hidden"
        style={{ backgroundColor: "hsl(var(--card))" }}
      >
        {loading ? (
          <div className="space-y-0">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3">
                <Skeleton className="h-8 w-8 rounded-full shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3 w-3/4 rounded-none" style={{ background: "#D9CEBC" }} />
                  <Skeleton className="h-2.5 w-1/4 rounded-none" style={{ background: "#D9CEBC" }} />
                </div>
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-sm font-body text-muted-foreground">
              No activity yet — start exploring to stamp your passport.
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

function ActivityRow({ item, index }: { item: ActivityItem; index: number }) {
  const ActionIcon = actionIcons[item.action]
  const CategoryIcon = categoryIcons[item.category]
  const actionColor = actionAccents[item.action]
  const categoryColor = categoryAccents[item.category]

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      className="flex items-center gap-3 px-4 py-3 hover:bg-parchment-dark/5 transition-colors cursor-default border-b border-border/30 last:border-b-0"
    >
      <div
        className="flex items-center justify-center w-8 h-8 rounded-none shrink-0"
        style={{ backgroundColor: actionColor + "20", color: actionColor }}
      >
        <ActionIcon className="h-4 w-4" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm leading-snug truncate font-body" style={{ color: "#10262A" }}>
          {describeAction(item)}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          <CategoryIcon className="h-3 w-3" style={{ color: categoryColor }} />
          <span className="text-[10px] font-body capitalize opacity-70" style={{ color: "#10262A" }}>
            {item.category}
          </span>
          <span className="text-[10px] opacity-30" style={{ color: "#10262A" }}>·</span>
          <span className="text-[10px] font-mono opacity-50" style={{ color: "#10262A" }}>
            {timeAgo(item.timestamp)}
          </span>
        </div>
      </div>
    </motion.div>
  )
}
