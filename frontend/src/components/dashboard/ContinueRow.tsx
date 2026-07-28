import { cn } from "@/lib/utils"
import { Card, CardContent, Badge, ScrollArea, Skeleton } from "@/components/ui"
import { Clock, Tv, UtensilsCrossed, Music, History } from "lucide-react"
import { motion } from "framer-motion"
import type { RecentItem, Category } from "../../types"

// ── Helpers ─────────────────────────────────────────────────────────

const categoryIcons: Record<Category, React.ElementType> = {
  anime: Tv,
  restaurant: UtensilsCrossed,
  music: Music,
}

const categoryGradients: Record<Category, string> = {
  anime: "from-violet-500 to-fuchsia-500",
  restaurant: "from-amber-500 to-orange-500",
  music: "from-emerald-500 to-teal-500",
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

// ── Component ───────────────────────────────────────────────────────

interface ContinueRowProps {
  items: RecentItem[]
  loading: boolean
}

export function ContinueRow({ items, loading }: ContinueRowProps) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2.5">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
          <History className="h-4 w-4 text-white" />
        </div>
        <h2 className="text-base font-semibold">Continue where you left off</h2>
      </div>

      {loading ? (
        <div className="flex gap-4 overflow-hidden">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="w-44 shrink-0 space-y-2">
              <Skeleton className="h-24 w-full rounded-xl" />
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border px-4 py-6 text-center">
          <p className="text-sm text-muted-foreground">
            Nothing here yet — start exploring to build your history
          </p>
        </div>
      ) : (
        <ScrollArea className="-mx-1 px-1">
          {items.map((item, i) => (
            <RecentCard key={item.id} item={item} index={i} />
          ))}
        </ScrollArea>
      )}
    </section>
  )
}

// ── Card ─────────────────────────────────────────────────────────────

function RecentCard({ item, index }: { item: RecentItem; index: number }) {
  const Icon = categoryIcons[item.category]
  const gradient = categoryGradients[item.category]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      whileHover={{ scale: 1.03 }}
      className="snap-start"
    >
      <Card className="group w-44 shrink-0 overflow-hidden cursor-pointer transition-shadow duration-300 hover:shadow-md hover:shadow-primary/5">
        {/* Image / Gradient fallback */}
        <div className="relative h-24 overflow-hidden">
          {item.imageUrl ? (
            <img
              src={item.imageUrl}
              alt={item.title}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
              loading="lazy"
            />
          ) : (
            <div
              className={cn(
                "h-full w-full bg-gradient-to-br flex items-center justify-center",
                gradient
              )}
            >
              <Icon className="h-8 w-8 text-white/40" />
            </div>
          )}

          <Badge
            variant="secondary"
            className="absolute top-2 left-2 text-[10px] capitalize"
          >
            {item.category}
          </Badge>
        </div>

        <CardContent className="p-2.5 space-y-1">
          <h3 className="text-xs font-semibold leading-snug line-clamp-2">
            {item.title}
          </h3>
          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>{timeAgo(item.viewedAt)}</span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
