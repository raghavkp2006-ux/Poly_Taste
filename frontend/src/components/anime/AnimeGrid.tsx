import { Card, CardContent } from "@/components/ui"

export function AnimeGrid({ animes, onSelect }: { animes: any[], onSelect: (anime: any) => void }) {
  if (!animes || animes.length === 0) {
    return <div className="text-center text-muted-foreground p-8">No anime found.</div>
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {animes.map(anime => (
        <Card 
          key={anime.mal_id} 
          className="overflow-hidden cursor-pointer hover:ring-2 ring-primary transition-all group"
          onClick={() => onSelect(anime)}
        >
          <div className="relative aspect-[3/4] overflow-hidden">
            <img 
              src={anime.images?.jpg?.image_url || anime.coverImage?.large || anime.cover_image} 
              alt={anime.title}
              className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            {anime.score && (
              <div className="absolute top-2 right-2 bg-black/70 text-white text-xs font-bold px-2 py-1 rounded">
                ★ {anime.score}
              </div>
            )}
          </div>
          <CardContent className="p-3">
            <h4 className="font-semibold text-sm line-clamp-2" title={anime.title}>{anime.title}</h4>
            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
              {anime.genres ? anime.genres.join(", ") : (anime.genres_raw || []).join(", ")}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
