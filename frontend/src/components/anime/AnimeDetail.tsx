import { useEffect, useState } from "react"
import { api } from "@/api"
import { getHighResImageUrl } from "@/lib/utils"
import { Button, Skeleton } from "@/components/ui"
import { AnimeGrid } from "./AnimeGrid"
import { ArrowLeft, ExternalLink } from "lucide-react"
import { domainColor, domainAlpha, colors, errorAlpha } from "../../tokens"
import { Card, LineRail, StationBadge } from "../interchange"

export function AnimeDetail({
  anime,
  onBack,
  onSelect,
}: {
  anime: any
  onBack: () => void
  onSelect: (anime: any) => void
}) {
  const mal_id = anime.mal_id || anime.idMal || anime.id

  const [reviews,  setReviews]  = useState<any[]>([])
  const [loadingR, setLoadingR] = useState(true)
  const [errR,     setErrR]     = useState(false)

  const [videos,   setVideos]   = useState<any[]>([])
  const [loadingV, setLoadingV] = useState(true)
  const [errV,     setErrV]     = useState(false)

  const [news,     setNews]     = useState<any[]>([])
  const [loadingN, setLoadingN] = useState(true)
  const [errN,     setErrN]     = useState(false)

  const [recs,     setRecs]     = useState<any[]>([])
  const [loadingP, setLoadingP] = useState(true)
  const [errP,     setErrP]     = useState(false)

  useEffect(() => {
    if (!mal_id) return
    api.anime.getReviews(mal_id)
      .then((r: any) => setReviews((r as any)?.reviews || []))
      .catch(() => setErrR(true))
      .finally(() => setLoadingR(false))
    api.anime.getVideos(mal_id)
      .then((r: any) => setVideos((r as any)?.videos || []))
      .catch(() => setErrV(true))
      .finally(() => setLoadingV(false))
    api.anime.getNews(mal_id)
      .then((r: any) => setNews((r as any)?.articles || []))
      .catch(() => setErrN(true))
      .finally(() => setLoadingN(false))
    api.anime.recommend(mal_id, false)
      .then((r: any) => setRecs((r as any)?.recommendations || []))
      .catch(() => setErrP(true))
      .finally(() => setLoadingP(false))
  }, [mal_id])

  const imgSrc = getHighResImageUrl(
    anime.images?.jpg?.large_image_url ||
    anime.coverImage?.extraLarge ||
    anime.images?.jpg?.image_url ||
    anime.cover_image ||
    anime.imageUrl
  )

  let genres: string[] = []
  if (Array.isArray(anime.genres)) {
    genres = anime.genres
  } else if (typeof anime.genres === "string") {
    genres = [anime.genres]
  } else if (Array.isArray(anime.genres_raw)) {
    genres = anime.genres_raw
  } else if (typeof anime.genres_raw === "string") {
    genres = [anime.genres_raw]
  }

  return (
    <div className="space-y-8 pb-16 animate-in fade-in">
      {/* Back */}
      <Button
        variant="ghost"
        onClick={onBack}
        className="mb-2 -ml-1"
        style={{ color: domainColor.anime }}
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Browse
      </Button>

      {/* Hero info */}
      <Card className="flex flex-col md:flex-row gap-6 p-6 relative overflow-hidden">
        <LineRail domain="anime" />
        {imgSrc && (
          <img
            src={imgSrc}
            alt={anime.title}
            className="w-full md:w-52 rounded-xl object-cover shadow-lg"
            style={{ boxShadow: `0 0 40px ${domainAlpha("anime", 0.3)}` }}
          />
        )}
        <div className="flex-1 space-y-4">
          <h1 className="text-2xl md:text-3xl font-display font-bold text-foreground">
            {anime.title}
          </h1>

          {/* Genre tags */}
          {genres.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {genres.map((g: string) => (
                <span
                  key={g}
                  className="text-xs font-mono px-3 py-0.5 rounded-full"
                  style={{
                    color:            domainColor.anime,
                    backgroundColor:  domainAlpha("anime", 0.15),
                    border:           `1px solid ${domainAlpha("anime", 0.3)}`,
                  }}
                >
                  {g}
                </span>
              ))}
            </div>
          )}

          {anime.score && (
            <div className="inline-flex items-center gap-2">
              <StationBadge value={anime.score} domain="anime" size={48} />
            </div>
          )}

          {/* Synopsis */}
          <p className="text-sm font-sans text-muted-foreground leading-relaxed">
            {anime.synopsis || anime.description || "No synopsis available."}
          </p>
        </div>
      </Card>

      {/* Videos */}
      <Section title="Videos & Trailers" accent={domainColor.anime}>
        {loadingV ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="aspect-video w-full rounded-xl" />
            ))}
          </div>
        ) : errV ? (
          <ErrorMsg />
        ) : videos.length === 0 ? (
          <Empty msg="No videos found." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map((v) => (
              <Card
                key={v.id.videoId}
                className="overflow-hidden flex flex-col relative"
              >
                <iframe
                  className="w-full aspect-video"
                  src={`https://www.youtube.com/embed/${v.id.videoId}`}
                  title={v.snippet.title}
                  allowFullScreen
                />
                <div className="p-3 text-xs font-sans text-muted-foreground line-clamp-2">
                  {v.snippet.title}
                </div>
              </Card>
            ))}
          </div>
        )}
      </Section>

      {/* Reviews */}
      <Section title="Reviews" accent={domainColor.anime}>
        {loadingR ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <Skeleton key={i} className="h-28 w-full rounded-xl" />
            ))}
          </div>
        ) : errR ? (
          <ErrorMsg />
        ) : reviews.length === 0 ? (
          <Empty msg="No reviews found." />
        ) : (
          <div className="space-y-4">
            {reviews.slice(0, 5).map((r) => (
              <Card
                key={r.id}
                className="p-4 relative"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-sans font-semibold text-sm text-foreground">
                    {r.user?.name || "User"}
                  </span>
                  <span
                    className="text-xs font-mono"
                    style={{ color: domainColor.anime }}
                  >
                    ★ {r.score}
                  </span>
                </div>
                <p
                  className="text-xs font-sans text-muted-foreground line-clamp-4"
                  dangerouslySetInnerHTML={{ __html: r.body || r.summary }}
                />
              </Card>
            ))}
          </div>
        )}
      </Section>

      {/* News */}
      <Section title="Latest News" accent={domainColor.anime}>
        {loadingN ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : errN ? (
          <ErrorMsg />
        ) : news.length === 0 ? (
          <Empty msg="No news found." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {news.slice(0, 6).map((n) => (
              <a
                key={n.link}
                href={n.link}
                target="_blank"
                rel="noreferrer"
                className="block group"
              >
                <Card className="p-4 transition-all duration-200 group-hover:border-[#FF7A59]/40 relative">
                <h4
                  className="font-sans font-medium text-sm line-clamp-2 mb-1.5 text-foreground group-hover:text-[#FF7A59] transition-colors"
                >
                  {n.title}
                </h4>
                <div className="flex justify-between items-center text-[10px] text-muted-foreground font-mono">
                  <span>{new Date(n.published).toLocaleDateString()}</span>
                  <ExternalLink className="w-3 h-3" />
                </div>
                </Card>
              </a>
            ))}
          </div>
        )}
      </Section>

      {/* Similar Anime */}
      <Section title="Similar Anime" accent={domainColor.anime}>
        {loadingP ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="aspect-[3/4] w-full rounded-xl" />
            ))}
          </div>
        ) : errP ? (
          <ErrorMsg />
        ) : recs.length === 0 ? (
          <Empty msg="No similar anime found." />
        ) : (
          <AnimeGrid
            animes={recs.slice(0, 5)}
            onSelect={(a) => {
              window.scrollTo({ top: 0, behavior: "smooth" })
              onBack()
              setTimeout(() => onSelect(a), 0)
            }}
          />
        )}
      </Section>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────

function Section({
  title,
  accent,
  children,
}: {
  title: string
  accent: string
  children: React.ReactNode
}) {
  return (
    <section className="space-y-4">
      <div className="flex items-center gap-3">
        <LineRail domain="anime" />
        <h2 className="text-base font-display font-semibold tracking-wide text-foreground pl-3">
          {title}
        </h2>
      </div>
      {children}
    </section>
  )
}

function ErrorMsg() {
  return (
    <div
      className="text-sm font-sans p-4 rounded-lg"
      style={{
        background: errorAlpha(0.06),
        border: `1px solid ${errorAlpha(0.15)}`,
        color: colors.error,
      }}
    >
      Failed to load — please try again later.
    </div>
  )
}

function Empty({ msg }: { msg: string }) {
  return (
    <p className="text-sm font-sans text-muted-foreground">{msg}</p>
  )
}
