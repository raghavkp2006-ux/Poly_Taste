import { motion } from "framer-motion"

const ANIME_ACCENT = "#FF7A59"

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
  const imgSrc =
    anime.images?.jpg?.image_url ||
    anime.coverImage?.large ||
    anime.cover_image

  const genres: string[] = anime.genres
    ? anime.genres
    : anime.genres_raw || []

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
      className="cursor-pointer group glow-edge-anime"
      onClick={() => onSelect(anime)}
      style={{
        background: "rgba(18,24,31,0.75)",
        backdropFilter: "blur(10px)",
        border: "1px solid rgba(255,255,255,0.05)",
        borderRadius: "0.75rem",
        overflow: "hidden",
      }}
    >
      {/* Domain accent bar */}
      <div
        className="h-0.5 w-full"
        style={{ background: `linear-gradient(90deg, ${ANIME_ACCENT} 0%, transparent 80%)` }}
      />

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
            style={{ background: `${ANIME_ACCENT}10` }}
          >
            ◈
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
          <div
            className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold"
            style={{
              background: "rgba(10,14,20,0.85)",
              color: ANIME_ACCENT,
              border: `1px solid ${ANIME_ACCENT}40`,
            }}
          >
            ★ {anime.score}
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
    </motion.div>
  )
}
