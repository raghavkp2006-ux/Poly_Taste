import { useEffect, useState } from "react"
import { api } from "@/api"
import { Button, Skeleton } from "@/components/ui"
import { AnimeGrid } from "./AnimeGrid"
import { ArrowLeft, ExternalLink } from "lucide-react"

export function AnimeDetail({ anime, onBack, onSelect }: { anime: any, onBack: () => void, onSelect: (anime: any) => void }) {
  const mal_id = anime.mal_id || anime.idMal
  
  const [reviews, setReviews] = useState<any[]>([])
  const [loadingReviews, setLoadingReviews] = useState(true)
  const [reviewsError, setReviewsError] = useState(false)

  const [videos, setVideos] = useState<any[]>([])
  const [loadingVideos, setLoadingVideos] = useState(true)
  const [videosError, setVideosError] = useState(false)

  const [news, setNews] = useState<any[]>([])
  const [loadingNews, setLoadingNews] = useState(true)
  const [newsError, setNewsError] = useState(false)

  const [recommendations, setRecommendations] = useState<any[]>([])
  const [loadingRecs, setLoadingRecs] = useState(true)
  const [recsError, setRecsError] = useState(false)

  useEffect(() => {
    if (!mal_id) return

    api.anime.getReviews(mal_id).then(res => setReviews(res.reviews || [])).catch(() => setReviewsError(true)).finally(() => setLoadingReviews(false))
    api.anime.getVideos(mal_id).then(res => setVideos(res.videos || [])).catch(() => setVideosError(true)).finally(() => setLoadingVideos(false))
    api.anime.getNews(mal_id).then(res => setNews(res.articles || [])).catch(() => setNewsError(true)).finally(() => setLoadingNews(false))
    api.anime.recommend(mal_id, false).then(res => setRecommendations(res.recommendations || [])).catch(() => setRecsError(true)).finally(() => setLoadingRecs(false))

  }, [mal_id])

  return (
    <div className="space-y-8 animate-in fade-in pb-16">
      <Button variant="ghost" onClick={onBack} className="mb-4">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Browse
      </Button>

      {/* Header Info */}
      <div className="flex flex-col md:flex-row gap-6">
        <img 
          src={anime.images?.jpg?.large_image_url || anime.coverImage?.extraLarge || anime.images?.jpg?.image_url || anime.cover_image} 
          alt={anime.title}
          className="w-full md:w-64 rounded-xl shadow-lg object-cover"
        />
        <div className="flex-1 space-y-4">
          <h1 className="text-3xl font-bold">{anime.title}</h1>
          <div className="flex gap-2 flex-wrap">
            {(anime.genres || anime.genres_raw || []).map((g: string) => (
              <span key={g} className="bg-primary/10 text-primary px-3 py-1 rounded-full text-sm font-medium">
                {g}
              </span>
            ))}
          </div>
          {anime.score && <div className="text-lg font-semibold">Score: {anime.score} / 10</div>}
          <p className="text-muted-foreground leading-relaxed">{anime.synopsis || anime.description || "No synopsis available."}</p>
        </div>
      </div>

      {/* Videos Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Videos & Trailers</h2>
        {loadingVideos ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => <Skeleton key={i} className="aspect-video w-full rounded-xl" />)}
          </div>
        ) : videosError ? (
          <div className="text-muted-foreground bg-muted p-4 rounded-lg">Failed to load videos.</div>
        ) : videos.length === 0 ? (
          <div className="text-muted-foreground">No videos found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map(v => (
              <div key={v.id.videoId} className="rounded-xl overflow-hidden bg-card border shadow-sm flex flex-col">
                <iframe
                  className="w-full aspect-video"
                  src={`https://www.youtube.com/embed/${v.id.videoId}`}
                  title={v.snippet.title}
                  allowFullScreen
                />
                <div className="p-3 text-sm font-medium line-clamp-2">{v.snippet.title}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Reviews Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Reviews</h2>
        {loadingReviews ? (
          <div className="space-y-4">
            {[1, 2].map(i => <Skeleton key={i} className="h-32 w-full rounded-xl" />)}
          </div>
        ) : reviewsError ? (
          <div className="text-muted-foreground bg-muted p-4 rounded-lg">Failed to load reviews.</div>
        ) : reviews.length === 0 ? (
          <div className="text-muted-foreground">No reviews found.</div>
        ) : (
          <div className="space-y-4">
            {reviews.slice(0, 5).map(r => (
              <div key={r.id} className="bg-card border p-4 rounded-xl shadow-sm">
                <div className="font-semibold mb-2">{r.user?.name || "User"} <span className="text-muted-foreground font-normal text-sm ml-2">Score: {r.score}</span></div>
                <p className="text-muted-foreground text-sm line-clamp-4" dangerouslySetInnerHTML={{ __html: r.body || r.summary }}></p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* News Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Latest News</h2>
        {loadingNews ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}
          </div>
        ) : newsError ? (
          <div className="text-muted-foreground bg-muted p-4 rounded-lg">Failed to load news.</div>
        ) : news.length === 0 ? (
          <div className="text-muted-foreground">No news found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {news.slice(0, 6).map(n => (
              <a key={n.link} href={n.link} target="_blank" rel="noreferrer" className="block bg-card border p-4 rounded-lg hover:ring-2 ring-primary transition-all shadow-sm">
                <h4 className="font-medium line-clamp-2 mb-1">{n.title}</h4>
                <div className="flex justify-between items-center text-xs text-muted-foreground">
                  <span>{new Date(n.published).toLocaleDateString()}</span>
                  <ExternalLink className="w-3 h-3" />
                </div>
              </a>
            ))}
          </div>
        )}
      </section>

      {/* Similar Anime Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Similar Anime</h2>
        {loadingRecs ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="aspect-[3/4] w-full rounded-xl" />)}
          </div>
        ) : recsError ? (
          <div className="text-muted-foreground bg-muted p-4 rounded-lg">Failed to load recommendations.</div>
        ) : recommendations.length === 0 ? (
          <div className="text-muted-foreground">No similar anime found.</div>
        ) : (
          <AnimeGrid animes={recommendations.slice(0, 5)} onSelect={(anime) => {
            window.scrollTo({ top: 0, behavior: 'smooth' })
            onBack()
            setTimeout(() => onSelect(anime), 0)
          }} />
        )}
      </section>
    </div>
  )
}
