import { useEffect, useState } from "react"
import { api } from "./api"
import { TopographicBackground } from "./components/ui/TopographicBackground"
import { Component as LoginPage } from "./components/ui/animated-characters-login-page"
import { Sidebar } from "./components/dashboard/Sidebar"
import { DashboardHome } from "./components/dashboard/DashboardHome"
import { AnimeGrid } from "./components/anime/AnimeGrid"
import { AnimeDetail } from "./components/anime/AnimeDetail"
import { cn } from "@/lib/utils"
import {
  Button,
  Input,
  Switch,
} from "./components/ui"
import { Search, Loader2 } from "lucide-react"
import type { PageId } from "./types"

export default function App() {
  const [user, setUser] = useState<{ user_id: string } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const hash = window.location.hash
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
        .then(setUser)
        .catch(() => setUser(null))
        .finally(() => setLoading(false))
    }
  }, [])

  if (loading) {
    return (
      <>
        <TopographicBackground />
        <div className="flex h-screen items-center justify-center bg-transparent">
          <div className="flex flex-col items-center gap-4">
            <div
              className="w-10 h-10 rounded-none animate-pulse"
              style={{ backgroundColor: "hsl(var(--sidebar-accent))" }}
            />
            <p className="font-mono text-xs tracking-widest uppercase text-muted-foreground">
              Loading passport…
            </p>
          </div>
        </div>
      </>
    )
  }

  if (!user) {
    return (
      <>
        <TopographicBackground />
        <LoginPage />
      </>
    )
  }

  return (
    <>
      <TopographicBackground />
      <DashboardLayout userId={user.user_id} onLogout={() => {
        api.auth.logout().then(() => setUser(null))
      }} />
    </>
  )
}

// ── Dashboard Shell ─────────────────────────────────────────────────

function DashboardLayout({ userId, onLogout }: { userId: string; onLogout: () => void }) {
  const [currentPage, setCurrentPage] = useState<PageId>("home")
  const [selectedAnime, setSelectedAnime] = useState<any | null>(null)
  const [collapsed, setCollapsed] = useState(false)

  const handleNavigate = (page: PageId, item?: any) => {
    if (page === "anime") {
      if (item) {
        setSelectedAnime({
          mal_id: item.id,
          title: item.title,
          cover_image: item.imageUrl,
          score: item.score,
          synopsis: item.reason
        });
      } else {
        setSelectedAnime(null);
      }
    }
    setCurrentPage(page);
  };

  return (
    <div className="flex min-h-screen bg-transparent">
      <Sidebar
        currentPage={currentPage}
        onNavigate={handleNavigate}
        onLogout={onLogout}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
      />

      <div className={cn("flex-1 transition-all duration-300", collapsed ? "md:ml-[72px]" : "md:ml-[240px]")}>
        {currentPage === "home" && (
          <DashboardHome userName={userId} onLogout={onLogout} onNavigate={handleNavigate} />
        )}
        {currentPage === "anime" && (
          <PageWrapper title="Anime" onLogout={onLogout} userName={userId}>
            <AnimeModule externalSelectedAnime={selectedAnime} onExternalSelectAnime={setSelectedAnime} />
          </PageWrapper>
        )}
        {currentPage === "restaurants" && (
          <PageWrapper title="Restaurants" onLogout={onLogout} userName={userId}>
            <RestaurantModule />
          </PageWrapper>
        )}
        {currentPage === "music" && (
          <PageWrapper title="Music" onLogout={onLogout} userName={userId}>
            <MusicPlaceholder />
          </PageWrapper>
        )}
        {currentPage === "settings" && (
          <PageWrapper title="Settings" onLogout={onLogout} userName={userId}>
            <SettingsPlaceholder />
          </PageWrapper>
        )}
      </div>
    </div>
  )
}

// ── Page wrappers ────────────────────────────────────────────────────

function PageWrapper({
  children,
  title: _title,
  onLogout: _onLogout,
  userName: _userName,
}: {
  children: React.ReactNode
  title: string
  onLogout: () => void
  userName: string
}) {
  return (
    <div className="flex flex-col min-h-screen">
      <div className="flex-1 p-4 md:p-6 lg:p-8 pb-24 md:pb-8">
        {children}
      </div>
    </div>
  )
}

function SettingsPlaceholder() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-display tracking-wide text-foreground">Preferences</h2>
      <div className="border border-border/40 overflow-hidden" style={{ background: "hsl(var(--card))" }}>
        <div className="p-6 space-y-4">
          <p className="text-sm font-body text-muted-foreground">
            Toggle dark mode from the top bar on the Home page. More options stamp in soon.
          </p>
        </div>
      </div>
    </div>
  )
}

function MusicPlaceholder() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-4">
      <div
        className="w-14 h-14 flex items-center justify-center"
        style={{ backgroundColor: "#C6318C" }}
      >
        <span className="text-2xl text-parchment font-display">♪</span>
      </div>
      <h2 className="text-xl font-display tracking-wide text-foreground">No tracks matched yet</h2>
      <p className="text-sm font-body text-muted-foreground max-w-sm">
        Connect Spotify to start your music passport — we'll stamp every listen.
      </p>
      <a
        href={api.auth.loginUrl}
        className="inline-flex items-center gap-2 rounded-none px-5 py-2.5 text-sm font-display tracking-wide text-parchment transition-opacity hover:opacity-90"
        style={{ backgroundColor: "#C6318C" }}
      >
        Connect Spotify
      </a>
    </div>
  )
}

// ── Anime sub-module ────────────────────────────────────────────────

function AnimeModule({ externalSelectedAnime, onExternalSelectAnime }: { externalSelectedAnime?: any, onExternalSelectAnime?: (anime: any) => void }) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])
  const [upcoming, setUpcoming] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingUpcoming, setLoadingUpcoming] = useState(true)
  const [localSelectedAnime, setLocalSelectedAnime] = useState<any | null>(null)

  const selectedAnime = externalSelectedAnime !== undefined ? externalSelectedAnime : localSelectedAnime
  const setSelectedAnime = onExternalSelectAnime || setLocalSelectedAnime

  useEffect(() => {
    api.anime.getUpcoming()
      .then(res => setUpcoming((res as { upcoming?: any[] }).upcoming || []))
      .catch(console.error)
      .finally(() => setLoadingUpcoming(false))
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query) {
      setResults([])
      return
    }
    setLoading(true)
    try {
      setResults(await api.anime.search(query))
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  if (selectedAnime) {
    return <AnimeDetail anime={selectedAnime} onBack={() => setSelectedAnime(null)} onSelect={setSelectedAnime} />
  }

  const showResults = query && results.length > 0

  return (
    <div className="space-y-8 animate-in fade-in">
      <div className="flex items-center justify-between rounded-none border border-border/40 p-4" style={{ background: "hsl(var(--card))" }}>
        <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-md">
          <Input placeholder="Search anime by title..." value={query} onChange={e => setQuery(e.target.value)} />
          <Button type="submit"><Search className="h-4 w-4 mr-2" /> Search</Button>
        </form>
      </div>

      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="animate-spin w-8 h-8 text-primary" /></div>
      ) : showResults ? (
        <section>
          <h2 className="text-2xl font-display tracking-wide text-foreground mb-4">Search Results</h2>
          <AnimeGrid animes={results} onSelect={setSelectedAnime} />
        </section>
      ) : (
        <section>
          <h2 className="text-2xl font-display tracking-wide text-foreground mb-4 flex items-center gap-2">
            <span className="w-2 h-2 inline-block" style={{ backgroundColor: "#E8A23D" }} />
            Upcoming Anime
          </h2>
          {loadingUpcoming ? (
            <div className="flex justify-center p-12"><Loader2 className="animate-spin w-8 h-8 text-primary" /></div>
          ) : (
            <AnimeGrid animes={upcoming} onSelect={setSelectedAnime} />
          )}
        </section>
      )}
    </div>
  )
}

// ── Restaurant sub-module ───────────────────────────────────────────

function RestaurantModule() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [personalize, setPersonalize] = useState(false)
  const [lat, setLat] = useState<number | null>(null)
  const [lng, setLng] = useState<number | null>(null)
  const [manualLocation, setManualLocation] = useState("")
  const [locationStatus, setLocationStatus] = useState<"idle" | "prompting" | "granted" | "denied">("idle")

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationStatus("denied")
      return
    }

    setLocationStatus("prompting")
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLat(position.coords.latitude)
        setLng(position.coords.longitude)
        setLocationStatus("granted")
      },
      (error) => {
        console.warn("[geolocation]", error.message)
        setLocationStatus("denied")
      },
      { timeout: 10000, maximumAge: 300000 }
    )
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query) return
    setLoading(true)
    try {
      const res = await api.restaurants.search(query, lat ?? undefined, lng ?? undefined)
      setResults(res.results || [])
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const handleManualSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!manualLocation.trim() || !query) return
    setLoading(true)
    try {
      const res = await api.restaurants.search(query, undefined, undefined, manualLocation.trim())
      setResults(res.results || [])
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const handleRecommend = async (id: string) => {
    setLoading(true)
    try {
      const res = await api.restaurants.recommend(id, personalize)
      setResults(res.recommendations || [])
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <div className="rounded-none border border-border/40 p-4" style={{ background: "hsl(var(--card))" }}>
        {/* Location banner */}
        <div className="mb-4">
          {locationStatus === "prompting" && (
            <div className="flex items-center gap-2 text-xs font-mono" style={{ color: "#E8A23D" }}>
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Requesting your location…</span>
            </div>
          )}
          {locationStatus === "granted" && lat && lng && (
            <div className="flex items-center gap-2 text-xs font-mono" style={{ color: "#4A9B8E" }}>
              <span>Location locked — searching near {lat.toFixed(2)}, {lng.toFixed(2)}</span>
            </div>
          )}
          {locationStatus === "denied" && (
            <div className="space-y-2">
              <p className="text-xs font-mono" style={{ color: "#B23A2E" }}>
                Location access denied — enter a city or ZIP to search nearby.
              </p>
              <form onSubmit={handleManualSearch} className="flex gap-2">
                <Input
                  placeholder="City or ZIP code"
                  value={manualLocation}
                  onChange={(e) => setManualLocation(e.target.value)}
                  className="h-8 text-xs"
                />
                <Button type="submit" size="sm" variant="outline" className="h-8 text-xs">Set</Button>
              </form>
            </div>
          )}
        </div>

        {/* Search + Personalize row */}
        <div className="flex items-center justify-between gap-4">
          <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-md">
            <Input placeholder="Search restaurants..." value={query} onChange={e => setQuery(e.target.value)} />
            <Button type="submit"><Search className="h-4 w-4" /></Button>
          </form>
          <div className="flex items-center gap-2">
            <label className="text-xs font-body text-muted-foreground">Personalize</label>
            <Switch checked={personalize} onCheckedChange={setPersonalize} />
          </div>
        </div>
      </div>

      {loading && <div className="flex justify-center p-8"><Loader2 className="animate-spin text-primary" /></div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.isArray(results) && results.map((restaurant) => {
          const id = restaurant.place_id || restaurant.id
          return (
            <div key={id} className="ticket-perf overflow-hidden cursor-pointer transition-shadow duration-300 hover:shadow-lg" style={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}>
              <div className="p-4 pb-3 space-y-2">
                <h3 className="text-sm font-body font-semibold leading-snug line-clamp-2" style={{ color: "hsl(var(--card-foreground))" }}>
                  {restaurant.name}
                </h3>
                <p className="text-xs font-mono" style={{ color: "#B23A2E" }}>
                  {restaurant.rating ? `${restaurant.rating} ★` : 'No rating'}
                </p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono">
                  {Array.isArray(restaurant.types) ? restaurant.types.slice(0, 3).join(" · ") : ""}
                </p>
                <p className="text-xs text-muted-foreground line-clamp-2 font-body">
                  {restaurant.vicinity || restaurant.formatted_address}
                </p>
              </div>
              <div className="px-4 pb-4 flex flex-col gap-2">
                <button
                  onClick={() => handleRecommend(id)}
                  className="text-[11px] font-mono uppercase tracking-wider px-3 py-1.5 transition-opacity hover:opacity-80 rounded-none"
                  style={{ backgroundColor: "#B23A2E", color: "#EFE6D8" }}
                >
                  Similar
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  )
}

export function TasteProfileModule() {
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.taste.getProfile()
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader2 className="animate-spin mx-auto mt-8" />

  if (!profile) return <p className="text-center text-muted-foreground font-body">Failed to load taste profile.</p>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="border border-border/40 overflow-hidden" style={{ background: "hsl(var(--card))" }}>
        <div className="px-5 py-4 border-b border-border/30">
          <h3 className="text-sm font-display tracking-wide uppercase" style={{ color: "hsl(var(--card-foreground))" }}>Top Genres</h3>
        </div>
        <div className="p-5 space-y-3">
          {profile.top_genres.map((g: any) => (
            <li key={g.genre} className="flex justify-between font-body text-sm" style={{ color: "hsl(var(--card-foreground))" }}>
              <span>{g.genre}</span>
              <span className="font-mono text-xs">{Math.round(g.score * 100)}%</span>
            </li>
          ))}
        </div>
      </div>

      <div className="border border-border/40 overflow-hidden" style={{ background: "hsl(var(--card))" }}>
        <div className="px-5 py-4 border-b border-border/30">
          <h3 className="text-sm font-display tracking-wide uppercase" style={{ color: "hsl(var(--card-foreground))" }}>Top Sentiments</h3>
        </div>
        <div className="p-5 space-y-3">
          {Object.entries(profile.top_sentiments || {}).map(([s, score]: any) => (
            <li key={s} className="flex justify-between font-body text-sm capitalize" style={{ color: "hsl(var(--card-foreground))" }}>
              <span>{s}</span>
              <span className="font-mono text-xs">{Math.round(score * 100)}%</span>
            </li>
          ))}
        </div>
      </div>

      <div className="md:col-span-2 border border-border/40 overflow-hidden" style={{ background: "hsl(var(--card))" }}>
        <div className="px-5 py-4 border-b border-border/30">
          <h3 className="text-sm font-display tracking-wide uppercase" style={{ color: "hsl(var(--card-foreground))" }}>Likes Activity</h3>
        </div>
        <div className="p-5 flex gap-8">
          <div>
            <p className="text-2xl font-display" style={{ color: "hsl(var(--card-foreground))" }}>{profile.likes_count?.anime || 0}</p>
            <p className="text-xs font-body text-muted-foreground">Anime Liked</p>
          </div>
          <div>
            <p className="text-2xl font-display" style={{ color: "hsl(var(--card-foreground))" }}>{profile.likes_count?.restaurants || 0}</p>
            <p className="text-xs font-body text-muted-foreground">Restaurants Liked</p>
          </div>
        </div>
      </div>
    </div>
  )
}
