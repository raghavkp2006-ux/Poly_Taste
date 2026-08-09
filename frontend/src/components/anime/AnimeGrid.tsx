import { motion } from "framer-motion"
import { getHighResImageUrl } from "@/lib/utils"
import { Card, LineRail, StationBadge } from "../interchange"
import { domainAlpha, domainColor } from "../../tokens"

export function AnimeGrid({
  animes,
  onSelect,
}: {
  animes: any[]
  onSelect: (anime: any) => void
}) {
  if (!animes || animes.length === 0) {
    return (
      <div
        className="text-center py-10 rounded-xl"
        style={{
          color: "#7B8794",
          background: "rgba(18,24,31,0.5)",
          border: "1px solid rgba(255,255,255,0.05)",
        }}
      >
        No anime found.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {animes.map((anime, i) => (
        <AnimeSignalCard
          key={anime.mal_id ?? i}
          anime={anime}
          index={i}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}

function AnimeSignalCard({
  anime,
  index,
  onSelect,
}: {
  anime: any
  index: number
  onSelect: (anime: any) => void
}) {
  const imgSrc = getHighResImageUrl(
    anime.images?.jpg?.image_url ||
    anime.coverImage?.large ||
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
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        delay:    index * 0.04,
        duration: 0.4,
        ease:     [0.22, 1, 0.36, 1],
      }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="h-full"
    >
      <Card
        className="cursor-pointer group h-full flex flex-col relative overflow-hidden"
        onClick={() => onSelect(anime)}
      >
        <LineRail domain="anime" />

        {/* Cover image */}
      <div className="relative aspect-[3/4] overflow-hidden">
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={anime.title}
            className="object-cover w-full h-full transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center text-4xl"
            style={{ background: domainAlpha("anime", 0.1) }}
          >
            <span style={{ color: domainColor.anime }}>◈</span>
          </div>
        )}

        {/* Image scrim */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to top, rgba(18,24,31,0.9) 0%, transparent 55%)",
          }}
        />

        {/* Score badge */}
        {anime.score && (
          <div className="absolute top-2 right-2">
            <StationBadge value={anime.score} domain="anime" size={32} />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3 space-y-1">
        <h4
          className="font-sans font-semibold text-xs line-clamp-2 text-foreground leading-snug"
          title={anime.title}
        >
          {anime.title}
        </h4>
        {genres.length > 0 && (
          <p
            className="text-[9px] font-sans line-clamp-1"
            style={{ color: "#7B8794" }}
          >
            {genres.slice(0, 2).join(" · ")}
          </p>
        )}
      </div>
      </Card>
    </motion.div>
  )
}
