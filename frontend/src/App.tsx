import { useEffect, useState } from "react"
import { api } from "./api"
import { AmbientBackground } from "./components/ui/AmbientBackground"
import { Component as LoginPage } from "./components/ui/animated-characters-login-page"
import { Sidebar } from "./components/dashboard/Sidebar"
import { DashboardHome } from "./components/dashboard/DashboardHome"
import { AnimeGrid } from "./components/anime/AnimeGrid"
import { AnimeDetail } from "./components/anime/AnimeDetail"
import { ConvergenceHalo } from "./components/dashboard/ConvergenceHalo"
import { OnboardingWizard } from "./components/onboarding/OnboardingWizard"
import { cn } from "@/lib/utils"
import { Button, Input, Switch } from "./components/ui"
import { Search, Loader2 } from "lucide-react"
import type { PageId } from "./types"

import { GLASS_PANEL, colors } from "./tokens"

// ── Domain accent constants ──────────────────────────────────────────
const FOOD_ACCENT  = colors.food
const MUSIC_ACCENT = colors.music

// ── Derive wizard resume step from OAuth redirect params ────────────
function detectResumeStep(): number {
  const params = new URLSearchParams(window.location.search)
  const spotifyDone = params.get("spotify") === "connected"
  const anilistDone = params.get("anilist") === "connected"

  // Clean params from URL without triggering a reload
  if (spotifyDone || anilistDone) {
    const clean = window.location.pathname + window.location.hash
    window.history.replaceState(null, "", clean)
  }

  if (spotifyDone && anilistDone) return 3 // Location step
  if (anilistDone)                return 3 // Location step
  if (spotifyDone)                return 2 // AniList step
  return 0
}

export default function App() {
  const [user,           setUser]           = useState<{ user_id: string } | null>(null)
  const [loading,        setLoading]        = useState(true)
  const [showOnboarding, setShowOnboarding] = useState(false)
  // Computed once on mount so it's stable across re-renders
  const [wizardStep]                        = useState(() => detectResumeStep())

  useEffect(() => {
    const hash  = window.location.hash
    const match = hash.match(/id_token=([^&]+)/)

    if (match) {
      const idToken = match[1]
      window.location.hash = ""
      api.auth.googleCallback(idToken)
        .then(() => window.location.reload())
        .catch(() => {
          window.location.hash = hash
          checkSession()
        })
      return
    }

    checkSession()

    function checkSession() {
      api.auth.me()
        .then((u) => {
          setUser(u)
          // ── Onboarding gate ──────────────────────────────────────
          const doneKey = `onboarding_done_${u.user_id}`
          if (localStorage.getItem(doneKey)) {
            // Already completed onboarding
            setShowOnboarding(false)
            return
          }
          // Check connection status; if endpoint is absent or all
          // connected, skip wizard; otherwise show it.
          api.connections.getStatus()
            .then((status) => {
              const fullyConnected = status.spotify && status.anilist
              if (fullyConnected) {
                localStorage.setItem(doneKey, "true")
                setShowOnboarding(false)
              } else {
                setShowOnboarding(true)
              }
            })
            .catch(() => {
              // /connections/status not yet live — show wizard so user
              // can still connect services opportunistically.
              setShowOnboarding(true)
            })
        })
        .catch(() => setUser(null))
        .finally(() => setLoading(false))
    }
  }, [])

  if (loading) {
    return (
      <>
        <AmbientBackground />
        <div className="flex h-screen items-center justify-center bg-transparent">
          <div className="flex flex-col items-center gap-4">
            {/* Convergence ring spinner */}
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #7C6CF0 0%, #3ED6C4 100%)",
                padding: 2,
                animation: "spin 1.2s linear infinite",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  borderRadius: "50%",
                  background: "#0A0E14",
                }}
              />
            </div>
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <p className="font-mono text-xs tracking-widest uppercase text-muted-foreground">
              Initializing…
            </p>
          </div>
        </div>
      </>
    )
  }

  if (!user) {
    return (
      <>
        <AmbientBackground />
        <LoginPage />
      </>
    )
  }

  if (showOnboarding) {
    return (
      <>
        <AmbientBackground />
        <OnboardingWizard
          userId={user.user_id}
          initialStep={wizardStep}
          onComplete={() => {
            localStorage.setItem(`onboarding_done_${user.user_id}`, "true")
            setShowOnboarding(false)
          }}
        />
      </>
    )
  }

  return (
    <>
      <AmbientBackground />
      <DashboardLayout
        userId={user.user_id}
        onLogout={() => {
          api.auth.logout().then(() => setUser(null))
        }}
      />
    </>
  )
}

// ── Dashboard shell ──────────────────────────────────────────────────

function DashboardLayout({
  userId,
  onLogout,
}: {
  userId: string
  onLogout: () => void
}) {
  const [currentPage,    setCurrentPage]    = useState<PageId>("home")
  const [selectedAnime,  setSelectedAnime]  = useState<any | null>(null)
  const [collapsed,      setCollapsed]      = useState(false)
  const [connections,    setConnections]    = useState<{ spotify: boolean; anilist: boolean; location: boolean } | null>(null)

  useEffect(() => {
    api.connections.getStatus()
      .then(setConnections)
      .catch((err) => {
        console.error("Failed to fetch connection status:", err)
        setConnections({ spotify: false, anilist: false, location: false })
      })
  }, [])

  const handleNavigate = (page: PageId, item?: any) => {
    if (page === "anime") {
      if (item) {
        setSelectedAnime({
          mal_id:       item.id,
          title:        item.title,
          cover_image:  item.imageUrl,
          score:        item.score,
          synopsis:     item.reason,
        })
      } else {
        setSelectedAnime(null)
      }
    }
    setCurrentPage(page)
  }

  return (
    <div className="flex min-h-screen bg-transparent">
      <Sidebar
        currentPage={currentPage}
        onNavigate={handleNavigate}
        onLogout={onLogout}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
        connections={connections}
      />

      <div
        className={cn(
          "flex-1 transition-all duration-300",
          collapsed ? "md:ml-[72px]" : "md:ml-[240px]"
        )}
      >
        {currentPage === "home" && (
          <DashboardHome
            userName={userId}
            onLogout={onLogout}
            onNavigate={handleNavigate}
            connections={connections}
          />
        )}
        {currentPage === "anime" && (
          <PageWrapper>
            <AnimeModule
              externalSelectedAnime={selectedAnime}
              onExternalSelectAnime={setSelectedAnime}
            />
          </PageWrapper>
        )}
        {currentPage === "restaurants" && (
          <PageWrapper>
            <RestaurantModule />
          </PageWrapper>
        )}
        {currentPage === "music" && (
          <PageWrapper>
            <MusicSection />
          </PageWrapper>
        )}
        {currentPage === "profile" && (
          <PageWrapper>
            <TasteProfileModule />
          </PageWrapper>
        )}
        {currentPage === "settings" && (
          <PageWrapper>
            <SettingsSection />
          </PageWrapper>
        )}
      </div>
    </div>
  )
}

// ── Page wrapper ─────────────────────────────────────────────────────

function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col min-h-screen">
      <div className="flex-1 p-4 md:p-6 lg:p-8 pb-24 md:pb-8">
        {children}
      </div>
    </div>
  )
}

// ── Settings section ─────────────────────────────────────────────────

function SettingsSection() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-display font-bold text-foreground">Preferences</h2>
      <div style={GLASS_PANEL}>
        <div className="p-6">
          <p className="text-sm font-sans text-muted-foreground">
            More settings coming soon. Your taste signals are already being tuned automatically.
          </p>
        </div>
      </div>
    </div>
  )
}

// ── Music section ────────────────────────────────────────────────────

function MusicSection() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-6">
      {/* Icon ring */}
      <div
        className="w-16 h-16 flex items-center justify-center rounded-full"
        style={{
          background: `linear-gradient(135deg, ${MUSIC_ACCENT}30, transparent)`,
          border: `1px solid ${MUSIC_ACCENT}40`,
          boxShadow: `0 0 32px ${MUSIC_ACCENT}30`,
        }}
      >
        <span style={{ fontSize: 28, color: MUSIC_ACCENT }}>♪</span>
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-display font-bold text-foreground">
          No music signals yet
        </h2>
        <p
          className="text-sm font-sans max-w-sm"
          style={{ color: "#7B8794" }}
        >
          Connect Spotify to activate your music signal — we'll learn your vibe from every listen.
        </p>
      </div>

      <div className="flex flex-col gap-2 items-center">
        <a
          href={api.auth.loginUrl}
          className="inline-flex items-center gap-2 rounded-xl px-6 py-2.5 text-sm font-sans font-semibold transition-all duration-200 hover:scale-[1.02] active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C6CF0] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0A0E14]"
          style={{
            backgroundColor: `${MUSIC_ACCENT}20`,
            color:            MUSIC_ACCENT,
            border:           `1px solid ${MUSIC_ACCENT}40`,
            boxShadow:        `0 0 20px ${MUSIC_ACCENT}20`,
          }}
        >
          Connect Spotify
        </a>
        <a href={api.anilist.loginUrl}>Connect AniList</a>
      </div>
    </div>
  )
}

// ── Anime sub-module ─────────────────────────────────────────────────

function AnimeModule({
  externalSelectedAnime,
  onExternalSelectAnime,
}: {
  externalSelectedAnime?: any
  onExternalSelectAnime?: (anime: any) => void
}) {
  const [query,          setQuery]          = useState("")
  const [results,        setResults]        = useState<any[]>([])
  const [upcoming,       setUpcoming]       = useState<any[]>([])
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [loading,        setLoading]        = useState(false)
  const [loadingUpcoming, setLoadingUpcoming] = useState(true)
  const [loadingRecs,    setLoadingRecs]    = useState(true)
  const [localSelected,  setLocalSelected]  = useState<any | null>(null)

  const selectedAnime  = externalSelectedAnime !== undefined ? externalSelectedAnime : localSelected
  const setSelectedAnime = onExternalSelectAnime || setLocalSelected

  useEffect(() => {
    api.anime.getUpcoming()
      .then((res) => setUpcoming((res as { upcoming?: any[] }).upcoming || []))
      .catch(console.error)
      .finally(() => setLoadingUpcoming(false))

    api.anime.getDashboardRecommendations()
      .then((res) => setRecommendations(res || []))
      .catch(console.error)
      .finally(() => setLoadingRecs(false))
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query) { setResults([]); return }
    setLoading(true)
    try {
      setResults(await api.anime.search(query))
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  if (selectedAnime) {
    return (
      <AnimeDetail
        anime={selectedAnime}
        onBack={() => setSelectedAnime(null)}
        onSelect={setSelectedAnime}
      />
    )
  }

  const showResults = query && results.length > 0

  return (
    <div className="space-y-8">
      {/* Search bar */}
      <div className="p-4 rounded-xl" style={GLASS_PANEL}>
        <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-lg">
          <Input
            placeholder="Search anime by title…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search anime"
          />
          <Button type="submit" id="btn-anime-search" style={{ backgroundColor: "#FF7A59", color: "#fff" }}>
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
        </form>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="animate-spin w-8 h-8" style={{ color: "#FF7A59" }} />
        </div>
      ) : showResults ? (
        <section>
          <SectionHeader title="Search Results" color="#FF7A59" />
          <AnimeGrid animes={results} onSelect={setSelectedAnime} />
        </section>
      ) : (
        <div className="space-y-10">
          <section>
            <SectionHeader title="Recommended for You" color="#FF7A59" />
            {loadingRecs ? (
              <div className="flex justify-center p-12">
                <Loader2 className="animate-spin w-8 h-8" style={{ color: "#FF7A59" }} />
              </div>
            ) : recommendations.length === 0 ? (
              <p className="text-sm text-muted-foreground">Add anime to your Taste Profile to get recommendations.</p>
            ) : (
              <AnimeGrid animes={recommendations} onSelect={setSelectedAnime} />
            )}
          </section>

          <section>
            <SectionHeader title="Upcoming Anime" color="#FF7A59" />
            {loadingUpcoming ? (
              <div className="flex justify-center p-12">
                <Loader2 className="animate-spin w-8 h-8" style={{ color: "#FF7A59" }} />
              </div>
            ) : (
              <AnimeGrid animes={upcoming} onSelect={setSelectedAnime} />
            )}
          </section>
        </div>
      )}
    </div>
  )
}

// ── Restaurant sub-module ────────────────────────────────────────────

function RestaurantModule() {
  const [query,          setQuery]          = useState("")
  const [results,        setResults]        = useState<any[]>([])
  const [loading,        setLoading]        = useState(false)
  const [personalize,    setPersonalize]    = useState(false)
  const [lat,            setLat]            = useState<number | null>(null)
  const [lng,            setLng]            = useState<number | null>(null)
  const [manualLocation, setManualLocation] = useState("")
  const [locationStatus, setLocationStatus] = useState<
    "idle" | "prompting" | "granted" | "denied"
  >("idle")

  useEffect(() => {
    if (!navigator.geolocation) { setLocationStatus("denied"); return }
    setLocationStatus("prompting")
    navigator.geolocation.getCurrentPosition(
      (pos) => { setLat(pos.coords.latitude); setLng(pos.coords.longitude); setLocationStatus("granted") },
      (err) => { console.warn("[geo]", err.message); setLocationStatus("denied") },
      { timeout: 10000, maximumAge: 300000 },
    )
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query) return
    setLoading(true)
    try {
      const res = await api.restaurants.search(query, lat ?? undefined, lng ?? undefined)
      setResults(res.results || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const handleManualSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!manualLocation.trim() || !query) return
    setLoading(true)
    try {
      const res = await api.restaurants.search(query, undefined, undefined, manualLocation.trim())
      setResults(res.results || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const handleRecommend = async (id: string) => {
    setLoading(true)
    try {
      const res = await api.restaurants.recommend(id, personalize)
      setResults(res.recommendations || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      {/* Search panel */}
      <div className="rounded-xl p-4 space-y-4" style={GLASS_PANEL}>
        {/* Location banner */}
        {locationStatus === "prompting" && (
          <div className="flex items-center gap-2 text-xs font-mono" style={{ color: FOOD_ACCENT }}>
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Requesting your location…</span>
          </div>
        )}
        {locationStatus === "granted" && lat && lng && (
          <div className="flex items-center gap-2 text-xs font-mono" style={{ color: "#3ED6C4" }}>
            <span>Location locked — {lat.toFixed(2)}, {lng.toFixed(2)}</span>
          </div>
        )}
        {locationStatus === "denied" && (
          <div className="space-y-2">
            <p className="text-xs font-mono" style={{ color: "#FF7A59" }}>
              Location denied — enter a city or ZIP to search nearby.
            </p>
            <form onSubmit={handleManualSearch} className="flex gap-2">
              <Input
                placeholder="City or ZIP code"
                value={manualLocation}
                onChange={(e) => setManualLocation(e.target.value)}
                className="h-8 text-xs"
                aria-label="Manual location"
              />
              <Button type="submit" size="sm" variant="outline" className="h-8 text-xs">
                Set
              </Button>
            </form>
          </div>
        )}

        {/* Search + personalize */}
        <div className="flex items-center justify-between gap-4">
          <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-md">
            <Input
              placeholder="Search restaurants…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search restaurants"
            />
            <Button
              type="submit"
              id="btn-restaurant-search"
              style={{ backgroundColor: FOOD_ACCENT + "25", color: FOOD_ACCENT, border: `1px solid ${FOOD_ACCENT}40` }}
            >
              <Search className="h-4 w-4" />
            </Button>
          </form>
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs font-sans text-muted-foreground">Personalize</label>
            <Switch checked={personalize} onCheckedChange={setPersonalize} />
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex justify-center p-8">
          <Loader2 className="animate-spin" style={{ color: FOOD_ACCENT }} />
        </div>
      )}

      {/* Results grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.isArray(results) && results.map((r) => {
          const id = r.place_id || r.id
          return (
            <div
              key={id}
              className="rounded-xl overflow-hidden cursor-pointer transition-all duration-300 hover:scale-[1.01] group glow-edge-food"
              style={GLASS_PANEL}
            >
              {/* Accent bar */}
              <div
                className="h-0.5 w-full"
                style={{ background: `linear-gradient(90deg, ${FOOD_ACCENT} 0%, transparent 80%)` }}
              />
              <div className="p-4 space-y-2">
                <h3 className="text-sm font-sans font-semibold leading-snug line-clamp-2 text-foreground">
                  {r.name}
                </h3>
                <p className="text-xs font-mono" style={{ color: FOOD_ACCENT }}>
                  {r.rating ? `${r.rating} ★` : "No rating"}
                </p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono">
                  {Array.isArray(r.types) ? r.types.slice(0, 3).join(" · ") : ""}
                </p>
                <p className="text-xs text-muted-foreground line-clamp-2 font-sans">
                  {r.vicinity || r.formatted_address}
                </p>
              </div>
              <div className="px-4 pb-4">
                <button
                  onClick={() => handleRecommend(id)}
                  id={`btn-similar-${id}`}
                  className="text-[11px] font-mono uppercase tracking-wider px-3 py-1.5 rounded-lg transition-all hover:scale-[1.02] active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#E3A857]"
                  style={{
                    backgroundColor: `${FOOD_ACCENT}18`,
                    color:            FOOD_ACCENT,
                    border:           `1px solid ${FOOD_ACCENT}35`,
                  }}
                >
                  Similar
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── TasteProfileModule (unchanged structure, updated styles) ─────────

export function TasteProfileModule() {
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.taste.getProfile()
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex h-64 items-center justify-center">
      <Loader2 className="animate-spin w-8 h-8" style={{ color: "#7C6CF0" }} />
    </div>
  )

  if (!profile) return (
    <div className="flex h-64 items-center justify-center">
      <p className="text-center text-muted-foreground font-sans">
        Failed to load taste profile.
      </p>
    </div>
  )

  // Calculate Convergence Score
  const domains = ['spotify', 'anime', 'restaurants'];
  const activeDomains = domains.filter(d => Object.keys(profile.breakdown?.[d] || {}).length > 0).length;
  const baseScore = activeDomains === 3 ? 80 : activeDomains === 2 ? 50 : 20;

  const allGenres: Record<string, number> = {};
  domains.forEach(d => {
    Object.keys(profile.breakdown?.[d] || {}).forEach(g => {
      allGenres[g] = (allGenres[g] || 0) + 1;
    });
  });
  
  const overlapping = Object.values(allGenres).filter(c => c > 1).length;
  const total = Object.keys(allGenres).length;
  const bonus = total > 0 ? Math.round((overlapping / total) * 20) : 0;
  const convergenceScore = Math.min(100, baseScore + bonus);

  // Convert profile object to sorted array for display
  const topGenres = Object.entries(profile.profile || {})
    .sort(([, a]: any, [, b]: any) => b - a)
    .slice(0, 5)

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header & Halo */}
      <div className="flex flex-col items-center justify-center py-8">
        <ConvergenceHalo score={convergenceScore} />
        <div className="text-center mt-6 space-y-2">
          <h2 className="text-2xl font-display font-bold text-foreground">
            Your Taste Profile
          </h2>
          <p className="text-sm font-sans text-muted-foreground max-w-md mx-auto">
            This is the unified model of your preferences across all domains.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ProfileCard title="Top Unified Signals">
          {topGenres.length > 0 ? (
            topGenres.map(([genre, score]: any) => (
              <li key={genre} className="flex justify-between font-sans text-sm capitalize text-foreground py-1">
                <span>{genre}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {Math.round(score)} pts
                </span>
              </li>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No signals detected yet.</p>
          )}
        </ProfileCard>

        <div className="space-y-6">
          <div style={GLASS_PANEL}>
            <div className="px-5 py-4 border-b border-white/[0.06]">
              <h3 className="text-sm font-display font-semibold uppercase tracking-wide text-foreground">
                Domain Activity
              </h3>
            </div>
            <div className="p-5 flex gap-8">
              <StatBlock label="Anime Liked"      value={Object.keys(profile.breakdown?.anime || {}).length}       color="#FF7A59" />
              <StatBlock label="AniList Genres"   value={Object.keys(profile.breakdown?.anilist || {}).length}     color="#4A90E2" />
              <StatBlock label="Foods Liked"      value={Object.keys(profile.breakdown?.restaurants || {}).length}  color="#E3A857" />
            </div>
          </div>
          
          <div style={GLASS_PANEL} className="p-5">
             <div className="flex items-center gap-3">
               <div
                 className="w-2 h-2 rounded-full"
                 style={{ backgroundColor: "#7C6CF0", boxShadow: "0 0 6px #7C6CF0" }}
               />
               <h3 className="text-sm font-display font-semibold uppercase tracking-wide text-foreground">
                 Spotify Connection
               </h3>
             </div>
             <p className="text-sm font-sans text-muted-foreground mt-2">
               {profile.spotify_connected 
                 ? "Your music taste is actively influencing your recommendations across anime and food."
                 : "Connect Spotify to unlock full cross-domain convergence."}
             </p>
             {!profile.spotify_connected && (
               <Button
                 className="mt-4"
                 style={{ backgroundColor: "#7C6CF0", color: "#fff" }}
                 onClick={() => window.location.href = "http://localhost:8000/spotify/login"}
               >
                 Connect Spotify
               </Button>
             )}
          </div>

          <div style={GLASS_PANEL} className="p-5">
             <div className="flex items-center gap-3">
               <div
                 className="w-2 h-2 rounded-full"
                 style={{ backgroundColor: "#4A90E2", boxShadow: "0 0 6px #4A90E2" }}
               />
               <h3 className="text-sm font-display font-semibold uppercase tracking-wide text-foreground">
                 AniList Connection
               </h3>
             </div>
             <p className="text-sm font-sans text-muted-foreground mt-2">
               {profile.anilist_connected 
                 ? "Your AniList profile is connected and actively influencing your recommendation signals."
                 : "Connect AniList to unlock full cross-domain convergence."}
             </p>
             {!profile.anilist_connected && (
               <Button
                 className="mt-4"
                 style={{ backgroundColor: "#4A90E2", color: "#fff" }}
                 onClick={() => window.location.href = "http://localhost:8000/anilist/login"}
               >
                 Connect AniList
               </Button>
             )}
          </div>
        </div>
      </div>

      {profile.anilist_watched && profile.anilist_watched.length > 0 && (
        <div style={GLASS_PANEL} className="p-5">
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: "#4A90E2", boxShadow: "0 0 6px #4A90E2" }}
            />
            <h3 className="text-sm font-display font-semibold uppercase tracking-wide text-foreground">
              Watched on AniList
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {profile.anilist_watched.map((item: any) => (
              <div 
                key={item.mal_id} 
                className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] flex flex-col justify-between"
              >
                <span className="text-sm font-sans font-medium text-foreground line-clamp-1">{item.title}</span>
                <div className="flex items-center justify-between mt-2 text-xs font-mono">
                  <span className="text-muted-foreground uppercase">{item.status.toLowerCase()}</span>
                  {item.score > 0 ? (
                    <span style={{ color: "#FF7A59" }}>{item.score} / 10</span>
                  ) : (
                    <span className="text-muted-foreground">Unscored</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────

function SectionHeader({ title, color }: { title: string; color: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
      />
      <h2 className="text-base font-display font-semibold tracking-wide uppercase text-foreground">
        {title}
      </h2>
    </div>
  )
}

function ProfileCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="overflow-hidden" style={GLASS_PANEL}>
      <div className="px-5 py-4 border-b border-white/[0.06]">
        <h3 className="text-sm font-display font-semibold uppercase tracking-wide text-foreground">
          {title}
        </h3>
      </div>
      <div className="p-5">
        <ul className="space-y-2">{children}</ul>
      </div>
    </div>
  )
}

function StatBlock({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  return (
    <div>
      <p
        className="text-2xl font-display font-bold"
        style={{ color }}
      >
        {value}
      </p>
      <p className="text-xs font-sans text-muted-foreground mt-0.5">{label}</p>
    </div>
  )
}
