import { cn } from "@/lib/utils"
import {
  Card,
  CardContent,
  Badge,
  ScrollArea,
  Skeleton,
  Button,
} from "@/components/ui"
import { Tv, UtensilsCrossed, Music, AlertCircle, Sparkles } from "lucide-react"
import { motion } from "framer-motion"
import type { Recommendation, Category } from "../../types"

// ── Category meta ───────────────────────────────────────────────────

const categoryMeta: Record<
  Category,
  { icon: React.ElementType; gradient: string; label: string }
> = {
  anime: {
    icon: Tv,
    gradient: "from-violet-500 to-fuchsia-500",
    label: "Anime",
  },
  restaurant: {
    icon: UtensilsCrossed,
    gradient: "from-amber-500 to-orange-500",
    label: "Restaurants",
  },
  music: {
    icon: Music,
    gradient: "from-emerald-500 to-teal-500",
    label: "Music",
  },
}

// ── Score badge color ───────────────────────────────────────────────

function scoreBadgeVariant(score: number): "success" | "secondary" | "outline" {
  if (score >= 90) return "success"
  if (score >= 75) return "secondary"
  return "outline"
}

// ── Main component ──────────────────────────────────────────────────

interface RecommendationRowProps {
  category: Category
  items: Recommendation[]
  loading: boolean
  error: string | null
  onRetry: () => void
}

export function RecommendationRow({
  category,
  items,
  loading,
  error,
  onRetry,
}: RecommendationRowProps) {
  const meta = categoryMeta[category]
  const Icon = meta.icon

  return (
    <section className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-2.5">
        <div
          className={cn(
            "flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br",
            meta.gradient
          )}
        >
          <Icon className="h-4 w-4 text-white" />
        </div>
        <h2 className="text-base font-semibold">{meta.label}</h2>
        {items.length > 0 && (
          <Badge variant="outline" className="ml-auto text-[10px]">
            {items.length} picks
          </Badge>
        )}
      </div>

      {/* Content states */}
      {loading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={onRetry} />
      ) : items.length === 0 ? (
        <EmptyState />
      ) : (
        <ScrollArea className="-mx-1 px-1">
          {items.map((item, i) => (
            <RecommendationCard key={item.id} item={item} index={i} category={category} />
          ))}
        </ScrollArea>
      )}
    </section>
  )
}

// ── Card ─────────────────────────────────────────────────────────────

function RecommendationCard({
  item,
  index,
  category,
}: {
  item: Recommendation
  index: number
  category: Category
}) {
  const meta = categoryMeta[category]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      whileHover={{ scale: 1.03 }}
      className="snap-start"
    >
      <Card className="group relative w-52 shrink-0 overflow-hidden transition-shadow duration-300 hover:shadow-lg hover:shadow-primary/10 cursor-pointer">
        {/* Image / Gradient fallback */}
        <div className="relative h-28 overflow-hidden">
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
                meta.gradient
              )}
            >
              <meta.icon className="h-10 w-10 text-white/40" />
            </div>
          )}

          {/* Score badge overlay */}
          <Badge
            variant={scoreBadgeVariant(item.score)}
            className="absolute top-2 right-2 text-[10px] shadow-sm"
          >
            {item.score}% match
          </Badge>
        </div>

        <CardContent className="p-3 space-y-1.5">
          <h3 className="text-sm font-semibold leading-snug line-clamp-2">
            {item.title}
          </h3>
          <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
            {item.reason}
          </p>
        </CardContent>
      </Card>
    </motion.div>
  )
}

// ── States ──────────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="flex gap-4 overflow-hidden">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="w-52 shrink-0 space-y-2">
          <Skeleton className="h-28 w-full rounded-xl" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-full" />
        </div>
      ))}
    </div>
  )
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string
  onRetry: () => void
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3">
      <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
      <p className="text-sm text-destructive flex-1">{message}</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Retry
      </Button>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-muted mb-3">
        <Sparkles className="h-5 w-5 text-muted-foreground" />
      </div>
      <p className="text-sm font-medium text-muted-foreground">
        Start rating things to get recommendations
      </p>
      <p className="text-xs text-muted-foreground/70 mt-1">
        The more you interact, the smarter your picks get
      </p>
    </div>
  )
}
