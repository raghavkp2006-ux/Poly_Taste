import {
  Tv,
  UtensilsCrossed,
  Music,
  AlertCircle,
} from "lucide-react"
import { motion } from "framer-motion"
import type { Recommendation, Category, PageId } from "../../types"

// ── Category meta ───────────────────────────────────────────────────

const categoryMeta: Record<
  Category,
  { icon: React.ElementType; color: string; label: string }
> = {
  anime: {
    icon: Tv,
    color: "#E8A23D",
    label: "Anime",
  },
  restaurant: {
    icon: UtensilsCrossed,
    color: "#B23A2E",
    label: "Restaurants",
  },
  music: {
    icon: Music,
    color: "#C6318C",
    label: "Music",
  },
}

// ── Main component ──────────────────────────────────────────────────

interface RecommendationRowProps {
  category: Category
  items: Recommendation[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onNavigate: (page: PageId) => void
}

export function RecommendationRow({
  category,
  items,
  loading,
  error,
  onRetry,
  onNavigate,
}: RecommendationRowProps) {
  const meta = categoryMeta[category]
  const Icon = meta.icon

  return (
    <section className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-2.5">
        <div
          className="flex items-center justify-center w-8 h-8 shrink-0"
          style={{ backgroundColor: meta.color }}
        >
          <Icon className="h-4 w-4 text-parchment" />
        </div>
        <h2 className="text-base font-display tracking-wide uppercase text-foreground">
          {meta.label}
        </h2>
        {items.length > 0 && (
          <span
            className="ml-auto text-[10px] font-mono uppercase tracking-widest px-2 py-0.5"
            style={{
              border: `1px solid ${meta.color}40`,
              color: meta.color,
            }}
          >
            {items.length} picks
          </span>
        )}
      </div>

      {/* Content states */}
      {loading ? (
        <LoadingSkeleton category={category} />
      ) : error ? (
        <ErrorStateWithRetry
          message={error}
          onRetry={onRetry}
          accent={meta.color}
        />
      ) : items.length === 0 ? (
        <CategoryEmptyState category={category} onNavigate={onNavigate} />
      ) : (
        <div className="flex gap-5 pb-4 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
          {items.map((item, i) => (
            <TicketStubCard
              key={item.id}
              item={item}
              index={i}
              category={category}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}
    </section>
  )
}

// ── Ticket-stub card ────────────────────────────────────────────────

function TicketStubCard({
  item,
  index,
  category,
  onNavigate,
}: {
  item: Recommendation
  index: number
  category: Category
  onNavigate: (page: PageId) => void
}) {
  const meta = categoryMeta[category]
  const accent = meta.color

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        delay: index * 0.07,
        duration: 0.5,
        ease: [0.22, 1, 0.36, 1],
      }}
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
      className="snap-start shrink-0 w-[210px] cursor-pointer"
      onClick={() => {
        if (category === "anime") onNavigate("anime")
        else if (category === "restaurant") onNavigate("restaurants")
        else if (category === "music") onNavigate("music")
      }}
    >
      <div
        className="relative overflow-hidden ticket-perf"
        style={{
          background: "#EFE6D8",
          border: `1px solid ${accent}40`,
        }}
      >
        {/* Category tab */}
        <div
          className="px-3 py-1 text-xs font-display uppercase tracking-widest text-center"
          style={{ backgroundColor: accent, color: "#EFE6D8" }}
        >
          {meta.label}
        </div>

        {/* Image */}
        <div className="relative h-32 overflow-hidden">
          {item.imageUrl ? (
            <img
              src={item.imageUrl}
              alt={item.title}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
              loading="lazy"
            />
          ) : (
            <div
              className="h-full w-full flex items-center justify-center"
              style={{ backgroundColor: accent + "25" }}
            >
              <meta.icon
                className="h-10 w-10"
                style={{ color: accent }}
              />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-3 space-y-2">
          <h3 className="text-sm font-body font-semibold leading-snug line-clamp-2 text-ink">
            {item.title}
          </h3>
          <p className="text-xs font-body text-ink/60 line-clamp-2 leading-relaxed">
            {item.reason}
          </p>
        </div>

        {/* Circular score stamp */}
        <div
          className="absolute bottom-3 right-3 w-11 h-11 rounded-full flex items-center justify-center text-parchment font-display text-sm tracking-wide"
          style={{
            backgroundColor: accent,
            boxShadow: "0 2px 8px rgba(16, 38, 42, 0.25)",
            animation: `stamp-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) ${index * 0.07 + 0.18}s both`,
          }}
        >
          {item.score}%
        </div>
      </div>
    </motion.div>
  )
}

// ── States ──────────────────────────────────────────────────────────

function LoadingSkeleton({ category }: { category: Category }) {
  const accent = categoryMeta[category].color
  return (
    <div className="flex gap-5 overflow-hidden">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="w-[210px] shrink-0 rounded-none overflow-hidden ticket-perf"
          style={{
            background: `linear-gradient(110deg, #EFE6D8 8%, #D9CEBC 18%, #EFE6D8 33%)`,
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
            border: `1px solid ${accent}40`,
          }}
        >
          <div className="h-10 animate-pulse" style={{ backgroundColor: accent + "30" }} />
          <div className="h-32 animate-pulse bg-parchment-dark/50" />
          <div className="p-3 space-y-2">
            <div className="h-3 w-3/4 rounded-sm bg-parchment-dark/60 animate-pulse" />
            <div className="h-3 w-full rounded-sm bg-parchment-dark/50 animate-pulse" />
          </div>
          <div className="absolute bottom-3 right-3 w-11 h-11 rounded-full bg-parchment-dark/40 animate-pulse" />
        </div>
      ))}
    </div>
  )
}

function ErrorStateWithRetry({
  message,
  onRetry,
  accent,
}: {
  message: string
  onRetry: () => void
  accent: string
}) {
  return (
    <div
      className="flex items-center gap-3 rounded-none border px-4 py-3"
      style={{ borderColor: accent + "50", background: accent + "10" }}
    >
      <AlertCircle className="h-5 w-5 shrink-0" style={{ color: accent }} />
      <p className="text-sm flex-1 text-foreground">{message}</p>
      <button
        onClick={onRetry}
        className="text-xs font-mono uppercase tracking-wider px-3 py-1.5 transition-colors hover:opacity-80"
        style={{ backgroundColor: accent, color: "#EFE6D8" }}
      >
        Retry
      </button>
    </div>
  )
}

// ── Empty states ────────────────────────────────────────────────────

const categoryEmptyCopy: Record<Category, { title: string; description: string; action?: string }> = {
  anime: {
    title: "No shows matched yet",
    description: "Rate some anime to start your music passport.",
    action: "Browse Anime",
  },
  restaurant: {
    title: "No restaurants matched yet",
    description: "Liked a spot recently? Add it here to build your culinary passport.",
  },
  music: {
    title: "No tracks matched yet",
    description: "Connect Spotify to start your music passport.",
  },
}

function CategoryEmptyState({
  category,
  onNavigate,
}: {
  category: Category
  onNavigate: (page: PageId) => void
}) {
  const meta = categoryMeta[category]
  const copy = categoryEmptyCopy[category]
  const Icon = meta.icon

  return (
    <div
      className="flex items-center gap-3 rounded-none border border-dashed px-4 py-4"
      style={{ borderColor: meta.color + "50" }}
    >
      <div
        className="flex items-center justify-center w-10 h-10 shrink-0"
        style={{ backgroundColor: meta.color + "20", color: meta.color }}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-foreground">{copy.title}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{copy.description}</p>
      </div>
      {copy.action && (
        <button
          onClick={() => {
            if (category === "anime") onNavigate("anime")
            else if (category === "restaurant") onNavigate("restaurants")
            else onNavigate("music")
          }}
          className="text-[11px] font-mono uppercase tracking-wider px-3 py-1.5 shrink-0 transition-opacity hover:opacity-80"
          style={{ backgroundColor: meta.color, color: "#EFE6D8" }}
        >
          {copy.action}
        </button>
      )}
    </div>
  )
}
