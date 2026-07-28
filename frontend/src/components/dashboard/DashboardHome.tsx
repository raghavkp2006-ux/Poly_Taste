import { useEffect, useState, useCallback } from "react"
import { api } from "../../api"
import { RecommendationRow } from "./RecommendationRow"
import { ContinueRow } from "./ContinueRow"
import { ActivityFeed } from "./ActivityFeed"
import { TopBar } from "./TopBar"
import { InteractiveHero } from "./InteractiveHero"
import {
  mockAnimeRecommendations,
  mockRestaurantRecommendations,
  mockMusicRecommendations,
  mockRecentItems,
  mockActivity,
} from "./mockData"
import type { Recommendation, RecentItem, ActivityItem, Category } from "../../types"

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
}

export function DashboardHome({ userName, onLogout }: DashboardHomeProps) {
  // Stable fetcher references
  const fetchAnime = useCallback(
    () => api.recommendations.getByCategory("anime"),
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
        
        <InteractiveHero userName={userName} />

        <div className="space-y-8">
          {categories.map(({ category, state }) => (
            <RecommendationRow
              key={category}
              category={category}
              items={state.data}
              loading={state.loading}
              error={state.error}
              onRetry={state.retry}
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
