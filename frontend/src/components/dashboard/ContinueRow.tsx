import { Skeleton } from "@/components/ui"
import { Clock, Tv, UtensilsCrossed, Music, History } from "lucide-react"
import { motion } from "framer-motion"
import type { RecentItem, Category } from "../../types"

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

interface ContinueRowProps {
  items: RecentItem[]
  loading: boolean
}

export function ContinueRow({ items, loading }: ContinueRowProps) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2.5">
        <div
          className="flex items-center justify-center w-8 h-8 shrink-0"
          style={{ backgroundColor: "hsl(var(--sidebar-accent))" }}
        >
          <History className="h-4 w-4 text-parchment" />
        </div>
        <h2 className="text-base font-display tracking-wide uppercase text-foreground">
          Continue where you left off
        </h2>
      </div>

      {loading ? (
        <div className="flex gap-4 overflow-hidden">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="w-44 shrink-0 rounded-none overflow-hidden ticket-perf">
              <Skeleton className="h-24 w-full rounded-none" style={{ background: "#EFE6D8" }} />
              <div className="p-2.5 space-y-2" style={{ background: "#EFE6D8" }}>
                <Skeleton className="h-3 w-3/4 rounded-none" style={{ background: "#D9CEBC" }} />
                <Skeleton className="h-2.5 w-1/2 rounded-none" style={{ background: "#D9CEBC" }} />
              </div>
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div
          className="rounded-none border border-dashed px-4 py-6 text-center"
          style={{ borderColor: "hsl(var(--border))" }}
        >
          <p className="text-sm font-body text-muted-foreground">
            No history yet — start exploring to build your passport trail.
          </p>
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto scrollbar-hide snap-x snap-mandatory pb-2">
          {items.map((item, i) => (
            <RecentCard key={item.id} item={item} index={i} />
          ))}
        </div>
      )}
    </section>
  )
}

function RecentCard({ item, index }: { item: RecentItem; index: number }) {
  const Icon = categoryIcons[item.category]
  const accent = categoryAccents[item.category]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        delay: index * 0.06,
        duration: 0.4,
        ease: [0.22, 1, 0.36, 1],
      }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="snap-start shrink-0 w-[180px] cursor-pointer"
    >
      <div
        className="relative overflow-hidden ticket-perf"
        style={{ background: "#EFE6D8", border: `1px solid ${accent}40` }}
      >
        <div className="relative h-24 overflow-hidden">
          {item.imageUrl ? (
            <img
              src={item.imageUrl}
              alt={item.title}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          ) : (
            <div
              className="h-full w-full flex items-center justify-center"
              style={{ backgroundColor: accent + "20" }}
            >
              <Icon className="h-8 w-8" style={{ color: accent + "80" }} />
            </div>
          )}
        </div>

        <div className="p-2.5 space-y-1">
          <h3 className="text-xs font-body font-semibold leading-snug line-clamp-2 text-ink">
            {item.title}
          </h3>
          <div className="flex items-center gap-1 text-[10px] text-ink/50 font-mono">
            <Clock className="h-3 w-3" />
            <span>{timeAgo(item.viewedAt)}</span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
