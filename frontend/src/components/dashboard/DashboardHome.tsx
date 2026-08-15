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
import { colors, fontFamily } from "../../tokens"
import { Card } from "../interchange"

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
      .catch((err) => {
        setState({ data: fallback, loading: false, error: err.message || "Failed to load" })
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
  connections?: { spotify: boolean; anilist: boolean; location: boolean } | null
}

export function DashboardHome({ userName, onLogout, onNavigate, connections }: DashboardHomeProps) {
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
    isConnected: boolean
  }[] = [
    { category: "anime",      state: anime,       isConnected: connections?.anilist ?? true },
    { category: "restaurant", state: restaurants, isConnected: true },
    { category: "music",      state: music,       isConnected: connections?.spotify ?? true },
  ]

  // Safe display name — handle email addresses (foo@bar.com → foo) and plain names
  const displayName = userName
    ? (userName.includes("@") ? userName.split("@")[0] : userName.split(" ")[0]) || "You"
    : "You"

  return (
    <div className="flex flex-col min-h-screen w-full overflow-x-hidden bg-[#FAFAFA] dark:bg-[#0A0A0B] transition-colors duration-150 ease-out text-[#18181B] dark:text-[#FAFAFA] font-sans">
      <TopBar userName={displayName} onLogout={onLogout} connections={connections} />

      <main className="flex-1 p-4 md:p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto w-full pb-24 md:pb-8 min-w-0">

        {/* Hero strip */}
        <Hero
          title={
            <span className="font-semibold tracking-tight text-4xl text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out">
              One signal for every{" "}
              <span className="text-[#2563EB] dark:text-[#3B82F6]">
                {displayName}
              </span>
              .
            </span>
          }
          subtitle="Discover your next obsession — personalized anime, culinary gems, and fresh tracks, all tuned to your taste."
          actions={[
            {
              label: "Explore Anime",
              href: "#",
              accentColor: "#2563EB",
              onClick: (e) => { e.preventDefault(); onNavigate("anime") },
            },
            {
              label: "Find Food",
              href: "#",
              accentColor: "#2563EB",
              onClick: (e) => { e.preventDefault(); onNavigate("restaurants") },
            },
            {
              label: "Discover Music",
              href: "#",
              accentColor: "#2563EB",
              onClick: (e) => { e.preventDefault(); onNavigate("music") },
            },
          ]}
        />

        {/* Convergence Halo — the signature moment */}
        <Card className="rounded-xl overflow-hidden shadow-[0_1px_3px_rgba(0,0,0,0.06),0_1px_2px_rgba(0,0,0,0.04)] dark:shadow-none border border-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out">
          <ConvergenceHalo />
        </Card>

        {/* Recommendation rows */}
        <div className="space-y-8">
          {categories.map(({ category, state, isConnected }) => (
            <RecommendationRow
              key={category}
              category={category}
              items={state.data}
              loading={state.loading}
              error={state.error}
              onRetry={state.retry}
              onNavigate={onNavigate}
              isConnected={isConnected}
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
