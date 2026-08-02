import { useEffect, useState, useCallback } from "react"
import { api } from "../../api"
import { RecommendationRow } from "./RecommendationRow"
import { ContinueRow } from "./ContinueRow"
import { ActivityFeed } from "./ActivityFeed"
import { TopBar } from "./TopBar"
import { Hero } from "../blocks/hero"
import { ConvergenceHalo } from "./ConvergenceHalo"
import {
  mockAnimeRecommendations,
  mockRestaurantRecommendations,
  mockMusicRecommendations,
  mockRecentItems,
  mockActivity,
} from "./mockData"
import type { Recommendation, RecentItem, ActivityItem, Category, PageId } from "../../types"

// ── Hook: fetch with mock fallback ───────────────────────────────────

interface FetchState<T> {
  data: T
  loading: boolean
  error: string | null
}

function useFetchWithFallback<T>(
  fetcher: () => Promise<T>,
  fallback: T,
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
        setState({ data: fallback, loading: false, error: null })
      })
  }, [fetcher, fallback])

  useEffect(() => {
    load()
  }, [load])

  return { ...state, retry: load }
}

// ── Component ────────────────────────────────────────────────────────

interface DashboardHomeProps {
  userName: string
  onLogout: () => void
  onNavigate: (page: PageId) => void
}

export function DashboardHome({ userName, onLogout, onNavigate }: DashboardHomeProps) {
  const fetchAnime       = useCallback(() => api.anime.getDashboardRecommendations(), [])
  const fetchRestaurants = useCallback(() => api.recommendations.getByCategory("restaurant"), [])
  const fetchMusic       = useCallback(() => api.recommendations.getByCategory("music"), [])
  const fetchRecent      = useCallback(() => api.recommendations.getRecent(), [])
  const fetchActivity    = useCallback(() => api.recommendations.getActivity(), [])

  const anime       = useFetchWithFallback<Recommendation[]>(fetchAnime,       mockAnimeRecommendations)
  const restaurants = useFetchWithFallback<Recommendation[]>(fetchRestaurants,  mockRestaurantRecommendations)
  const music       = useFetchWithFallback<Recommendation[]>(fetchMusic,        mockMusicRecommendations)
  const recent      = useFetchWithFallback<RecentItem[]>(fetchRecent,           mockRecentItems)
  const activity    = useFetchWithFallback<ActivityItem[]>(fetchActivity,       mockActivity)

  const categories: {
    category: Category
    state: FetchState<Recommendation[]> & { retry: () => void }
  }[] = [
    { category: "anime",      state: anime },
    { category: "restaurant", state: restaurants },
    { category: "music",      state: music },
  ]

  // Safe display name — handle email addresses (foo@bar.com → foo) and plain names
  const displayName = userName
    ? (userName.includes("@") ? userName.split("@")[0] : userName.split(" ")[0]) || "You"
    : "You"

  return (
    <div className="flex flex-col min-h-screen">
      <TopBar userName={displayName} onLogout={onLogout} />

      <main className="flex-1 p-4 md:p-6 lg:p-8 space-y-10 max-w-[1400px] mx-auto w-full pb-24 md:pb-8">

        {/* Hero strip */}
        <Hero
          title={
            <>
              One signal for every{" "}
              <span className="text-gradient-convergence">
                {displayName}
              </span>
              .
            </>
          }
          subtitle="Discover your next obsession — personalized anime, culinary gems, and fresh tracks, all tuned to your taste."
          actions={[
            {
              label: "Explore Anime",
              href: "#",
              accentColor: "#FF7A59",
              onClick: (e) => { e.preventDefault(); onNavigate("anime") },
            },
            {
              label: "Find Food",
              href: "#",
              accentColor: "#E3A857",
              onClick: (e) => { e.preventDefault(); onNavigate("restaurants") },
            },
            {
              label: "Discover Music",
              href: "#",
              accentColor: "#7C6CF0",
              onClick: (e) => { e.preventDefault(); onNavigate("music") },
            },
          ]}
        />

        {/* Convergence Halo — the signature moment */}
        <div
          className="rounded-2xl overflow-hidden"
          style={{
            background: "rgba(18,24,31,0.50)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255,255,255,0.05)",
          }}
        >
          <ConvergenceHalo />
        </div>

        {/* Recommendation rows */}
        <div className="space-y-10">
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
