import { useEffect, useState } from "react"
import { api } from "./api"
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Switch } from "./components/ui"
import { Search, Heart, Loader2, Calendar } from "lucide-react"
import { AnimeGrid } from "./components/anime/AnimeGrid"
import { AnimeDetail } from "./components/anime/AnimeDetail"
import { Component as LoginPage } from "./components/ui/animated-characters-login-page"
import { Sidebar } from "./components/dashboard/Sidebar"
import { DashboardHome } from "./components/dashboard/DashboardHome"
import type { PageId } from "./types"

export default function App() {
  const [user, setUser] = useState<{ user_id: string } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.auth.me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin h-8 w-8 text-primary" />
          <span className="text-sm text-muted-foreground">Loading Poly_Taste…</span>
        </div>
      </div>
    )
  }

  if (!user) {
    return <LoginPage />
  }

  return <DashboardLayout userId={user.user_id} onLogout={() => {
    api.auth.logout().then(() => setUser(null))
  }} />
}

// ── Dashboard Shell ─────────────────────────────────────────────────

function DashboardLayout({ userId, onLogout }: { userId: string; onLogout: () => void }) {
  const [currentPage, setCurrentPage] = useState<PageId>("home")

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} onLogout={onLogout} />

      {/* Main content area — offset by sidebar width */}
      <div className="flex-1 md:ml-[240px] transition-all duration-300">
        {currentPage === "home" && (
          <DashboardHome userName={userId} onLogout={onLogout} />
        )}
        {currentPage === "anime" && (
          <PageWrapper title="Anime" onLogout={onLogout} userName={userId}>
            <AnimeModule />
          </PageWrapper>
        )}
        {currentPage === "restaurants" && (
          <PageWrapper title="Restaurants" onLogout={onLogout} userName={userId}>
            <RestaurantModule />
          </PageWrapper>
        )}
        {currentPage === "music" && (
          <PageWrapper title="Music" onLogout={onLogout} userName={userId}>
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center mb-4">
                <span className="text-2xl">🎵</span>
              </div>
              <h2 className="text-xl font-bold mb-2">Music Recommendations</h2>
              <p className="text-sm text-muted-foreground max-w-sm">
                Connect your Spotify account to get personalized music recommendations based on your listening history.
              </p>
              <a
                href={api.auth.loginUrl}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#1DB954] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#1ed760] transition-colors"
              >
                Connect Spotify
              </a>
            </div>
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

// ── Page wrapper for sub-pages ──────────────────────────────────────

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

// ── Settings placeholder ────────────────────────────────────────────

function SettingsPlaceholder() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Settings</h2>
      <Card>
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Settings page coming soon. You can toggle dark mode from the top bar on the Home page.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}


function AnimeModule() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])
  const [upcoming, setUpcoming] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingUpcoming, setLoadingUpcoming] = useState(true)
  const [selectedAnime, setSelectedAnime] = useState<any | null>(null)

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
      <div className="flex items-center justify-between rounded-xl border bg-card p-4 shadow-sm">
        <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-md">
          <Input placeholder="Search anime by title..." value={query} onChange={e => setQuery(e.target.value)} />
          <Button type="submit"><Search className="h-4 w-4 mr-2" /> Search</Button>
        </form>
      </div>
      
      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="animate-spin w-8 h-8 text-primary" /></div>
      ) : showResults ? (
        <section>
          <h2 className="text-2xl font-bold mb-4">Search Results</h2>
          <AnimeGrid animes={results} onSelect={setSelectedAnime} />
        </section>
      ) : (
        <section>
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2"><Calendar className="w-6 h-6" /> Upcoming Anime</h2>
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

function RestaurantModule() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [personalize, setPersonalize] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query) return
    setLoading(true)
    try {
      const res = await api.restaurants.search(query)
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

  const handleLike = async (id: string) => {
    await api.restaurants.like(id)
    alert("Liked!")
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between rounded-lg border p-4">
        <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-md">
          <Input placeholder="Search restaurants..." value={query} onChange={e => setQuery(e.target.value)} />
          <Button type="submit"><Search className="h-4 w-4" /></Button>
        </form>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Personalize</label>
          <Switch checked={personalize} onCheckedChange={setPersonalize} />
        </div>
      </div>
      
      {loading && <Loader2 className="animate-spin mx-auto mt-8" />}
      
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {results.map((restaurant) => (
          <Card key={restaurant.place_id || restaurant.id} className="overflow-hidden flex flex-col justify-between">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-base line-clamp-2">{restaurant.name}</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="mb-2">
                <p className="text-sm font-bold">{restaurant.rating ? `${restaurant.rating} ★` : 'No rating'}</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{restaurant.types ? restaurant.types.join(", ") : ""}</p>
              </div>
              <p className="text-xs text-muted-foreground mb-4 line-clamp-3">{restaurant.vicinity || restaurant.formatted_address}</p>
              <div className="flex flex-col gap-2">
                <Button size="sm" variant="outline" onClick={() => handleRecommend(restaurant.place_id || restaurant.id)}>Similar</Button>
                <Button size="sm" variant="ghost" onClick={() => handleLike(restaurant.place_id || restaurant.id)}><Heart className="mr-2 h-4 w-4" /> Like</Button>
              </div>
            </CardContent>
          </Card>
        ))}
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
  
  if (!profile) return <p className="text-center text-muted-foreground">Failed to load taste profile.</p>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      <Card>
        <CardHeader>
          <CardTitle>Top Genres</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {profile.top_genres.map((g: any) => (
              <li key={g.genre} className="flex justify-between">
                <span>{g.genre}</span>
                <span className="font-medium">{Math.round(g.score * 100)}%</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Sentiments</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {Object.entries(profile.top_sentiments || {}).map(([s, score]: any) => (
              <li key={s} className="flex justify-between capitalize">
                <span>{s}</span>
                <span className="font-medium">{Math.round(score * 100)}%</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
      
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Likes Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-8">
            <div>
              <p className="text-2xl font-bold">{profile.likes_count?.anime || 0}</p>
              <p className="text-sm text-muted-foreground">Anime Liked</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{profile.likes_count?.restaurants || 0}</p>
              <p className="text-sm text-muted-foreground">Restaurants Liked</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
