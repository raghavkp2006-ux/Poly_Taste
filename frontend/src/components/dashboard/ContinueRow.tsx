import { Clock, Tv, UtensilsCrossed, Music, History } from "lucide-react"
import { motion } from "framer-motion"
import type { RecentItem, Category } from "../../types"

const DOMAIN_COLORS: Record<Category, string> = {
  anime:      "#FF7A59",
  restaurant: "#E3A857",
  music:      "#7C6CF0",
}

const DOMAIN_GLOW: Record<Category, string> = {
  anime:      "glow-edge-anime",
  restaurant: "glow-edge-food",
  music:      "glow-edge-music",
}

const CATEGORY_ICONS: Record<Category, React.ElementType> = {
  anime:      Tv,
  restaurant: UtensilsCrossed,
  music:      Music,
}

function timeAgo(isoDate: string): string {
  const seconds = Math.floor((Date.now() - new Date(isoDate).getTime()) / 1000)
  if (seconds < 60)  return "just now"
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60)  return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24)    return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

interface ContinueRowProps {
  items: RecentItem[]
  loading: boolean
}

export function ContinueRow({ items, loading }: ContinueRowProps) {
  return (
    <section className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <div
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: "#A0AEC0", boxShadow: "0 0 6px #A0AEC0" }}
        />
        <h2 className="text-sm font-display font-semibold tracking-wide uppercase text-foreground">
          Continue
        </h2>
        <History className="h-4 w-4 text-muted-foreground opacity-60" />
      </div>

      {loading ? (
        <div className="flex gap-3 overflow-hidden">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="w-[160px] shrink-0 rounded-xl overflow-hidden"
              style={{
                background: "rgba(18,24,31,0.6)",
                border: "1px solid rgba(255,255,255,0.05)",
              }}
            >
              <div className="h-20 skeleton-dark rounded-none" />
              <div className="p-2.5 space-y-1.5">
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
            No history yet — start exploring to build your trail.
          </p>
        </div>
      ) : (
        <div className="flex gap-3 overflow-x-auto scrollbar-hide snap-x snap-mandatory pb-2">
          {items.map((item, i) => (
            <RecentCard key={item.id} item={item} index={i} />
          ))}
        </div>
      )}
    </section>
  )
}

function RecentCard({ item, index }: { item: RecentItem; index: number }) {
  const Icon   = CATEGORY_ICONS[item.category]
  const accent = DOMAIN_COLORS[item.category]
  const glow   = DOMAIN_GLOW[item.category]

  return (
    <motion.div
      initial={{ opacity: 0, y: 14, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.05, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
      className="snap-start shrink-0 w-[200px] cursor-pointer group"
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
            background: `linear-gradient(90deg, ${accent} 0%, transparent 80%)`,
            opacity: 0.6,
          }}
        />

        {/* Image */}
        <div className="relative h-28 overflow-hidden">
          {item.imageUrl ? (
            <img
              src={item.imageUrl}
              alt={item.title}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div
              className="h-full w-full flex items-center justify-center"
              style={{ backgroundColor: `${accent}15` }}
            >
              <Icon className="h-10 w-10" style={{ color: accent, opacity: 0.5 }} />
            </div>
          )}
          {/* Scrim */}
          <div
            className="absolute inset-0"
            style={{ background: "linear-gradient(to top, rgba(18,24,31,0.9) 0%, transparent 60%)" }}
          />
        </div>

        <div className="p-3 space-y-1.5">
          <h3 className="text-xs font-sans font-semibold leading-snug line-clamp-2 text-foreground">
            {item.title}
          </h3>
          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono">
            <Clock className="h-3 w-3" />
            <span>{timeAgo(item.viewedAt)}</span>
          </div>
        </div>

        {/* Spacer to match RecommendationRow height feel */}
        <div className="h-2" />
      </div>
    </motion.div>
  )
}

