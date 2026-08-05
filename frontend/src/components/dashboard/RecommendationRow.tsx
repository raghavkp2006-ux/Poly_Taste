import { Tv, UtensilsCrossed, Music, AlertCircle } from "lucide-react"
import { motion } from "framer-motion"
import { getHighResImageUrl } from "../../lib/utils"
import type { Recommendation, Category, PageId } from "../../types"
import { api } from "../../api"

// ── Domain meta ──────────────────────────────────────────────────────

const DOMAIN: Record<Category, {
  icon: React.ElementType
  color: string
  glowEdge: string
  glowBg: string
  label: string
}> = {
  anime: {
    icon:     Tv,
    color:    "#FF7A59",
    glowEdge: "glow-edge-anime",
    glowBg:   "rgba(255,122,89,0.08)",
    label:    "Anime",
  },
  restaurant: {
    icon:     UtensilsCrossed,
    color:    "#E3A857",
    glowEdge: "glow-edge-food",
    glowBg:   "rgba(227,168,87,0.08)",
    label:    "Food",
  },
  music: {
    icon:     Music,
    color:    "#7C6CF0",
    glowEdge: "glow-edge-music",
    glowBg:   "rgba(124,108,240,0.08)",
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

  return (
    <section className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-3">
        {/* Domain dot */}
        <div
          className="w-2 h-2 rounded-full shrink-0"
          style={{
            backgroundColor: meta.color,
            boxShadow: `0 0 8px ${meta.color}`,
          }}
        />
        <h2 className="text-sm font-display font-semibold tracking-wide uppercase text-foreground">
          {meta.label}
        </h2>
        {/* Section icon */}
        <Icon className="h-4 w-4" style={{ color: meta.color, opacity: 0.7 }} />

        {isConnected && items.length > 0 && (
          <span
            className="ml-auto text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full"
            style={{
              border: `1px solid ${meta.color}30`,
              color:  meta.color,
              backgroundColor: `${meta.color}10`,
            }}
          >
            {items.length} signals
          </span>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <SignalCardSkeleton category={category} />
      ) : error ? (
        <ErrorState message={error} onRetry={onRetry} color={meta.color} />
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
  const accent = meta.color

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
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
      className="snap-start shrink-0 w-[200px] cursor-pointer group"
      onClick={handleClick}
    >
      {/* Glass card shell */}
      <div
        className={`relative overflow-hidden rounded-xl gradient-border ${meta.glowEdge} transition-all duration-300`}
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
              src={getHighResImageUrl(item.imageUrl)}
              alt={item.title}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />
          ) : (
            <div
              className="h-full w-full flex items-center justify-center"
              style={{ backgroundColor: `${accent}15` }}
            >
              <meta.icon className="h-10 w-10" style={{ color: accent, opacity: 0.5 }} />
            </div>
          )}
          {/* Image scrim */}
          <div
            className="absolute inset-0"
            style={{
              background: "linear-gradient(to top, rgba(18,24,31,0.9) 0%, transparent 60%)",
            }}
          />
        </div>

        {/* Content */}
        <div className="p-3 space-y-1.5">
          <h3 className="text-xs font-sans font-semibold leading-snug line-clamp-2 text-foreground">
            {item.title}
          </h3>
          <p className="text-[10px] font-sans text-muted-foreground line-clamp-2 leading-relaxed">
            {item.reason}
          </p>
        </div>

        {/* Score ring — bottom right */}
        <div className="absolute bottom-3 right-3">
          <ScoreRing score={item.score} color={accent} size={44} />
        </div>

        {/* Spacer for score ring */}
        <div className="h-6" />
      </div>
    </motion.div>
  )
}

// ── Score ring (SVG radial) ──────────────────────────────────────────

function ScoreRing({
  score,
  color,
  size = 44,
}: {
  score: number
  color: string
  size?: number
}) {
  const r      = (size - 6) / 2
  const circ   = 2 * Math.PI * r
  const offset = circ * (1 - score / 100)

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="rotate-[-90deg]"
      >
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="3"
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{
            filter: `drop-shadow(0 0 4px ${color}80)`,
            transition: "stroke-dashoffset 0.8s cubic-bezier(0.22, 1, 0.36, 1)",
          }}
        />
      </svg>
      {/* Score label */}
      <div
        className="absolute inset-0 flex items-center justify-center"
        style={{ fontSize: 10, fontFamily: "JetBrains Mono, monospace", color, fontWeight: 700 }}
      >
        {score}
      </div>
    </div>
  )
}

// ── Skeleton ─────────────────────────────────────────────────────────

function SignalCardSkeleton({ category }: { category: Category }) {
  const { color } = DOMAIN[category]
  return (
    <div className="flex gap-4 overflow-hidden">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="w-[200px] shrink-0 rounded-xl overflow-hidden"
          style={{
            background: "rgba(18,24,31,0.6)",
            border: `1px solid rgba(255,255,255,0.05)`,
          }}
        >
          <div
            className="h-1 w-full"
            style={{ backgroundColor: `${color}30` }}
          />
          <div
            className="h-28 skeleton-dark"
            style={{ borderRadius: 0 }}
          />
          <div className="p-3 space-y-2">
            <div className="h-2.5 w-3/4 rounded-full skeleton-dark" />
            <div className="h-2 w-full rounded-full skeleton-dark" />
            <div className="h-2 w-2/3 rounded-full skeleton-dark" />
          </div>
          {/* Score placeholder */}
          <div className="absolute bottom-3 right-3 w-11 h-11 rounded-full skeleton-dark" />
        </div>
      ))}
    </div>
  )
}

// ── Error state ───────────────────────────────────────────────────────

function ErrorState({
  message,
  onRetry,
  color,
}: {
  message: string
  onRetry: () => void
  color: string
}) {
  return (
    <div
      className="flex items-center gap-3 rounded-xl border px-4 py-3"
      style={{
        borderColor: `${color}30`,
        backgroundColor: `${color}08`,
      }}
    >
      <AlertCircle className="h-4 w-4 shrink-0" style={{ color }} />
      <p className="text-sm flex-1 font-sans text-foreground">{message}</p>
      <button
        onClick={onRetry}
        className="text-xs font-mono uppercase tracking-wider px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80"
        style={{ backgroundColor: `${color}20`, color }}
      >
        Retry
      </button>
    </div>
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
    <div
      className="flex items-center gap-3 rounded-xl border border-dashed px-4 py-4"
      style={{ borderColor: `${meta.color}30` }}
    >
      <div
        className="flex items-center justify-center w-10 h-10 rounded-lg shrink-0"
        style={{ backgroundColor: `${meta.color}15`, color: meta.color }}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-sans font-medium text-foreground">{title}</p>
        <p className="text-xs font-sans text-muted-foreground mt-0.5">{description}</p>
      </div>
      {action && (
        <button
          onClick={handleAction}
          className="text-[11px] font-mono uppercase tracking-wider px-3 py-1.5 rounded-lg shrink-0 transition-opacity hover:opacity-80"
          style={{ backgroundColor: `${meta.color}20`, color: meta.color }}
        >
          {action}
        </button>
      )}
    </div>
  )
}
