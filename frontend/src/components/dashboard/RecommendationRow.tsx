import { Tv, UtensilsCrossed, Music, AlertCircle } from "lucide-react"
import { motion } from "framer-motion"
import { getHighResImageUrl } from "../../lib/utils"
import type { Recommendation, Category, PageId } from "../../types"
import { api } from "../../api"
import { domainColor, domainAlpha, colors, fontFamily } from "../../tokens"
import { LineRail, StationBadge, Card } from "../interchange"

// ── Domain meta ──────────────────────────────────────────────────────

const DOMAIN: Record<Category, {
  icon: React.ElementType
  domainKey: "anime" | "food" | "music"
  label: string
}> = {
  anime: {
    icon:     Tv,
    domainKey: "anime",
    label:    "Anime",
  },
  restaurant: {
    icon:     UtensilsCrossed,
    domainKey: "food",
    label:    "Food",
  },
  music: {
    icon:     Music,
    domainKey: "music",
    label:    "Music",
  },
}

// ── Main component ───────────────────────────────────────────────────

interface RecommendationRowProps {
  category: Category
  items: Recommendation[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onNavigate: (page: PageId) => void
  isConnected?: boolean
}

export function RecommendationRow({
  category,
  items,
  loading,
  error,
  onRetry,
  onNavigate,
  isConnected = true,
}: RecommendationRowProps) {
  const meta = DOMAIN[category]
  const Icon = meta.icon
  const color = domainColor[meta.domainKey]

  return (
    <section className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-3">
        {/* Domain dot */}
        <div
          className="w-2 h-2 rounded-full shrink-0"
          style={{
            backgroundColor: color,
            boxShadow: `0 0 8px ${color}`,
          }}
        />
        <h2 
          className="text-sm font-semibold tracking-wide uppercase"
          style={{ fontFamily: fontFamily.display, color: colors.interchange }}
        >
          {meta.label}
        </h2>
        {/* Section icon */}
        <Icon className="h-4 w-4" style={{ color: color, opacity: 0.7 }} />

        {isConnected && items.length > 0 && (
          <span
            className="ml-auto text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full"
            style={{
              fontFamily: fontFamily.mono,
              border: `1px solid ${domainAlpha(meta.domainKey, 0.3)}`,
              color:  color,
              backgroundColor: domainAlpha(meta.domainKey, 0.1),
            }}
          >
            {items.length} signals
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex gap-4">
        {/* Line Rail on the left */}
        <LineRail domain={meta.domainKey} />

        <div className="flex-1 min-w-0">
          {loading ? (
            <SignalCardSkeleton category={category} />
          ) : error ? (
            <ErrorState message={error} onRetry={onRetry} category={category} />
          ) : (!isConnected || items.length === 0) ? (
            <EmptyState
              category={category}
              meta={meta}
              onNavigate={onNavigate}
              isConnected={isConnected}
            />
          ) : (
            <div className="flex gap-4 pb-3 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
              {items.map((item, i) => (
                <SignalCard
                  key={item.id}
                  item={item}
                  index={i}
                  category={category}
                  meta={meta}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

// ── Signal Card ──────────────────────────────────────────────────────

function SignalCard({
  item,
  index,
  category,
  meta,
  onNavigate,
}: {
  item: Recommendation
  index: number
  category: Category
  meta: typeof DOMAIN[Category]
  onNavigate: (page: PageId) => void
}) {
  const accent = domainColor[meta.domainKey]

  const handleClick = () => {
    if (category === "anime")      onNavigate("anime")
    else if (category === "restaurant") onNavigate("restaurants")
    else                           onNavigate("music")
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 14, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        delay:    index * 0.06,
        duration: 0.45,
        ease:     [0.22, 1, 0.36, 1],
      }}
      className="snap-start shrink-0 w-[200px]"
    >
      <Card
        domain={meta.domainKey}
        onClick={handleClick}
        className="h-full flex flex-col relative"
      >
        {/* Image */}
        <div className="relative h-28 overflow-hidden shrink-0">
          {item.imageUrl ? (
            <img
              src={getHighResImageUrl(item.imageUrl)}
              alt={item.title}
              className="h-full w-full object-cover transition-transform duration-500 hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div
              className="h-full w-full flex items-center justify-center"
              style={{ backgroundColor: domainAlpha(meta.domainKey, 0.15) }}
            >
              <meta.icon className="h-10 w-10" style={{ color: accent, opacity: 0.5 }} />
            </div>
          )}
          {/* Image scrim */}
          <div
            className="absolute inset-0"
            style={{
              background: `linear-gradient(to top, ${colors.paper} 0%, transparent 60%)`,
            }}
          />
        </div>

        {/* Content */}
        <div className="p-3 space-y-1.5 flex-1 relative z-10 -mt-4">
          <h3 className="text-sm font-semibold leading-snug line-clamp-2" style={{ color: colors.ink }}>
            {item.title}
          </h3>
          <p className="text-[10px] line-clamp-2 leading-relaxed" style={{ color: colors.interchange }}>
            {item.reason}
          </p>
        </div>

        {/* Score badge — bottom right */}
        <div className="absolute bottom-3 right-3">
          <StationBadge value={item.score} domain={meta.domainKey} size={40} />
        </div>
      </Card>
    </motion.div>
  )
}

// ── Skeleton ─────────────────────────────────────────────────────────

function SignalCardSkeleton({ category }: { category: Category }) {
  const meta = DOMAIN[category]
  return (
    <div className="flex gap-4 overflow-hidden">
      {Array.from({ length: 5 }).map((_, i) => (
        <Card key={i} className="w-[200px] shrink-0 overflow-hidden relative">
          <div
            className="h-1 w-full"
            style={{ backgroundColor: domainAlpha(meta.domainKey, 0.3) }}
          />
          <div
            className="h-28 skeleton-light"
            style={{ borderRadius: 0 }}
          />
          <div className="p-3 space-y-2">
            <div className="h-2.5 w-3/4 rounded-full skeleton-light" />
            <div className="h-2 w-full rounded-full skeleton-light" />
            <div className="h-2 w-2/3 rounded-full skeleton-light" />
          </div>
          <div className="absolute bottom-3 right-3 w-10 h-10 rounded-full skeleton-light" />
        </Card>
      ))}
    </div>
  )
}

// ── Error state ───────────────────────────────────────────────────────

function ErrorState({
  message,
  onRetry,
  category,
}: {
  message: string
  onRetry: () => void
  category: Category
}) {
  const meta = DOMAIN[category]
  const color = domainColor[meta.domainKey]
  return (
    <Card className="flex items-center gap-3 p-3">
      <AlertCircle className="h-4 w-4 shrink-0" style={{ color }} />
      <p className="text-sm flex-1" style={{ color: colors.ink }}>{message}</p>
      <button
        onClick={onRetry}
        className="text-xs uppercase tracking-wider px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80"
        style={{ fontFamily: fontFamily.mono, backgroundColor: domainAlpha(meta.domainKey, 0.1), color }}
      >
        Retry
      </button>
    </Card>
  )
}

// ── Empty state ────────────────────────────────────────────────────────

const EMPTY_COPY: Record<Category, { title: string; description: string; action?: string }> = {
  anime: {
    title:       "No anime signals yet",
    description: "Rate some shows to train your signal.",
    action:      "Browse Anime",
  },
  restaurant: {
    title:       "No food signals yet",
    description: "Like a spot nearby to build your culinary signal.",
  },
  music: {
    title:       "No music signals yet",
    description: "Connect Spotify to activate your music signal.",
  },
}

function EmptyState({
  category,
  meta,
  onNavigate,
  isConnected = true,
}: {
  category: Category
  meta: typeof DOMAIN[Category]
  onNavigate: (page: PageId) => void
  isConnected?: boolean
}) {
  const Icon = meta.icon
  const color = domainColor[meta.domainKey]

  let title = EMPTY_COPY[category].title
  let description = EMPTY_COPY[category].description
  let action = EMPTY_COPY[category].action

  const isMusic = category === "music"
  const isAnime = category === "anime"

  if (!isConnected) {
    if (isMusic) {
      title = "Connect Spotify to see real picks here"
      description = "Link your Spotify account to activate your music signal."
      action = "Connect Spotify"
    } else if (isAnime) {
      title = "Connect AniList to see real picks here"
      description = "Link your AniList account to activate your anime signal."
      action = "Connect AniList"
    }
  }

  const handleAction = () => {
    if (!isConnected) {
      if (isMusic) {
        window.location.href = api.auth.loginUrl
      } else if (isAnime) {
        window.location.href = api.anilist.loginUrl
      }
    } else {
      if (category === "anime")      onNavigate("anime")
      else if (category === "restaurant") onNavigate("restaurants")
      else                           onNavigate("music")
    }
  }

  return (
    <Card className="flex items-center gap-3 p-4">
      <div
        className="flex items-center justify-center w-10 h-10 rounded-lg shrink-0"
        style={{ backgroundColor: domainAlpha(meta.domainKey, 0.15), color: color }}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium" style={{ color: colors.ink }}>{title}</p>
        <p className="text-xs mt-0.5" style={{ color: colors.interchange }}>{description}</p>
      </div>
      {action && (
        <button
          onClick={handleAction}
          className="text-[11px] uppercase tracking-wider px-3 py-1.5 rounded-lg shrink-0 transition-opacity hover:opacity-80"
          style={{ fontFamily: fontFamily.mono, backgroundColor: domainAlpha(meta.domainKey, 0.1), color: color }}
        >
          {action}
        </button>
      )}
    </Card>
  )
}
