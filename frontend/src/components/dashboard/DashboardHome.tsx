import { useEffect, useState, useCallback } from "react"
import { api } from "../../api"
import { RecommendationRow } from "./RecommendationRow"
import { ContinueRow } from "./ContinueRow"
import { ActivityFeed } from "./ActivityFeed"
import { TopBar } from "./TopBar"
import { Hero } from "../blocks/hero"
import {
  mockAnimeRecommendations,
  mockRestaurantRecommendations,
  mockMusicRecommendations,
  mockRecentItems,
  mockActivity,
} from "./mockData"
import type { Recommendation, RecentItem, ActivityItem, Category, PageId } from "../../types"

// ── Hook: fetch with mock fallback ──────────────────────────────────

interface FetchState<T> {
  data: T
  loading: boolean
  error: string | null
}

function useFetchWithFallback<T>(
  fetcher: () => Promise<T>,
  fallback: T
): FetchState<T> & { retry: () => void } {
  const [state, setState] = useState<FetchState<T>>({
    data: fallback,
    loading: true,
    error: null,
  })

  const load = useCallback(() => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    fetcher()
      .then((data) => setState({ data, loading: false, error: null }))
      .catch(() => {
        // Silently fall back to mock data
        setState({ data: fallback, loading: false, error: null })
      })
  }, [fetcher, fallback])

  useEffect(() => {
    load()
  }, [load])

  return { ...state, retry: load }
}

// ── Component ───────────────────────────────────────────────────────

interface DashboardHomeProps {
  userName: string
  onLogout: () => void
  onNavigate: (page: PageId) => void
}

export function DashboardHome({ userName, onLogout, onNavigate }: DashboardHomeProps) {
  // Stable fetcher references
  const fetchAnime = useCallback(
    () => api.anime.getDashboardRecommendations(),
    []
  )
  const fetchRestaurants = useCallback(
    () => api.recommendations.getByCategory("restaurant"),
    []
  )
  const fetchMusic = useCallback(
    () => api.recommendations.getByCategory("music"),
    []
  )
  const fetchRecent = useCallback(() => api.recommendations.getRecent(), [])
  const fetchActivity = useCallback(() => api.recommendations.getActivity(), [])

  const anime = useFetchWithFallback<Recommendation[]>(
    fetchAnime,
    mockAnimeRecommendations
  )
  const restaurants = useFetchWithFallback<Recommendation[]>(
    fetchRestaurants,
    mockRestaurantRecommendations
  )
  const music = useFetchWithFallback<Recommendation[]>(
    fetchMusic,
    mockMusicRecommendations
  )
  const recent = useFetchWithFallback<RecentItem[]>(
    fetchRecent,
    mockRecentItems
  )
  const activity = useFetchWithFallback<ActivityItem[]>(
    fetchActivity,
    mockActivity
  )

  const categories: {
    category: Category
    state: FetchState<Recommendation[]> & { retry: () => void }
  }[] = [
    { category: "anime", state: anime },
    { category: "restaurant", state: restaurants },
    { category: "music", state: music },
  ]

  return (
    <div className="flex flex-col min-h-screen">
      <TopBar userName={userName} onLogout={onLogout} />

      <main className="flex-1 p-4 md:p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto w-full pb-24 md:pb-8">
        
        <Hero
          title={<>AI that works for <span className="bg-gradient-to-r from-stage-magenta via-parchment to-stage-magenta bg-clip-text text-transparent font-display">{userName.split(' ')[0]}</span>.</>}
          subtitle="Discover your next obsession, tailored just for you. Explore personalized anime, uncover hidden culinary gems, and dive into fresh music tracks."
          actions={[
            { label: "Explore Anime", href: "#", variant: "default", className: "bg-cel-amber text-ink hover:bg-cel-amber/90", onClick: (e) => { e.preventDefault(); onNavigate('anime') } },
            { label: "Find Food", href: "#", variant: "default", className: "bg-brick-red text-parchment hover:bg-brick-red/90", onClick: (e) => { e.preventDefault(); onNavigate('restaurants') } },
            { label: "Discover Music", href: "#", variant: "default", className: "bg-stage-magenta text-parchment hover:bg-stage-magenta/90", onClick: (e) => { e.preventDefault(); onNavigate('music') } }
          ]}
          titleClassName="text-5xl md:text-6xl font-extrabold font-display tracking-wide"
          subtitleClassName="text-lg md:text-xl max-w-[600px] font-body text-muted-foreground"
          actionsClassName="mt-8"
        />

        <div className="space-y-8">
          {categories.map(({ category, state }) => (
            <RecommendationRow
              key={category}
              category={category}
              items={state.data}
              loading={state.loading}
              error={state.error}
              onRetry={state.retry}
              onNavigate={onNavigate}
            />
          ))}
        </div>

        {/* Continue where you left off */}
        <ContinueRow items={recent.data} loading={recent.loading} />

        {/* Latest activity */}
        <ActivityFeed items={activity.data} loading={activity.loading} />
      </main>
    </div>
  )
}
