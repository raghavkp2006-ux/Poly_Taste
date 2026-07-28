import type { Recommendation, RecentItem, ActivityItem } from "../../types"

// ── Anime recommendations ───────────────────────────────────────────

export const mockAnimeRecommendations: Recommendation[] = [
  {
    id: "a1",
    title: "Frieren: Beyond Journey's End",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1015/138006l.jpg",
    reason: "Because you loved Violet Evergarden",
    score: 97,
    category: "anime",
  },
  {
    id: "a2",
    title: "Vinland Saga",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1500/103005l.jpg",
    reason: "Matches your taste for epic storytelling",
    score: 94,
    category: "anime",
  },
  {
    id: "a3",
    title: "Mob Psycho 100",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1286/110680l.jpg",
    reason: "Similar vibes to One Punch Man",
    score: 91,
    category: "anime",
  },
  {
    id: "a4",
    title: "Steins;Gate",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1935/127974l.jpg",
    reason: "You enjoy mind-bending plots",
    score: 96,
    category: "anime",
  },
  {
    id: "a5",
    title: "Bocchi the Rock!",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1448/139912l.jpg",
    reason: "Top pick for comedy fans",
    score: 89,
    category: "anime",
  },
  {
    id: "a6",
    title: "Chainsaw Man",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1806/126216l.jpg",
    reason: "Dark action, right up your alley",
    score: 92,
    category: "anime",
  },
]

// ── Restaurant recommendations ──────────────────────────────────────

export const mockRestaurantRecommendations: Recommendation[] = [
  {
    id: "r1",
    title: "Sukiyabashi Jiro",
    imageUrl: "",
    reason: "Because you liked Nobu",
    score: 98,
    category: "restaurant",
  },
  {
    id: "r2",
    title: "Eleven Madison Park",
    imageUrl: "",
    reason: "Matches your fine-dining taste",
    score: 95,
    category: "restaurant",
  },
  {
    id: "r3",
    title: "Dishoom King's Cross",
    imageUrl: "",
    reason: "You enjoy Indian-fusion cuisine",
    score: 90,
    category: "restaurant",
  },
  {
    id: "r4",
    title: "Tartine Manufactory",
    imageUrl: "",
    reason: "Perfect for bakery lovers",
    score: 87,
    category: "restaurant",
  },
  {
    id: "r5",
    title: "Momofuku Noodle Bar",
    imageUrl: "",
    reason: "You rated ramen spots highly",
    score: 93,
    category: "restaurant",
  },
]

// ── Music recommendations ───────────────────────────────────────────

export const mockMusicRecommendations: Recommendation[] = [
  {
    id: "m1",
    title: "Khruangbin – Con Todo El Mundo",
    imageUrl: "",
    reason: "Based on your lo-fi listening history",
    score: 94,
    category: "music",
  },
  {
    id: "m2",
    title: "Tame Impala – Currents",
    imageUrl: "",
    reason: "You listen to a lot of psychedelic rock",
    score: 92,
    category: "music",
  },
  {
    id: "m3",
    title: "Nujabes – Metaphorical Music",
    imageUrl: "",
    reason: "Similar to your chill-hop playlists",
    score: 96,
    category: "music",
  },
  {
    id: "m4",
    title: "Radiohead – In Rainbows",
    imageUrl: "",
    reason: "Matches your alternative taste",
    score: 90,
    category: "music",
  },
  {
    id: "m5",
    title: "Mac DeMarco – Salad Days",
    imageUrl: "",
    reason: "You liked similar indie artists",
    score: 88,
    category: "music",
  },
]

// ── Recently viewed ─────────────────────────────────────────────────

export const mockRecentItems: RecentItem[] = [
  {
    id: "a1",
    title: "Frieren: Beyond Journey's End",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1015/138006l.jpg",
    category: "anime",
    viewedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
  {
    id: "r2",
    title: "Eleven Madison Park",
    imageUrl: "",
    category: "restaurant",
    viewedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "m3",
    title: "Nujabes – Metaphorical Music",
    imageUrl: "",
    category: "music",
    viewedAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
  },
  {
    id: "a4",
    title: "Steins;Gate",
    imageUrl: "https://cdn.myanimelist.net/images/anime/1935/127974l.jpg",
    category: "anime",
    viewedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
]

// ── Activity feed ───────────────────────────────────────────────────

export const mockActivity: ActivityItem[] = [
  {
    id: "act1",
    action: "rated",
    itemTitle: "Spirited Away",
    detail: "5",
    category: "anime",
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
  },
  {
    id: "act2",
    action: "liked",
    itemTitle: "Sukiyabashi Jiro",
    category: "restaurant",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "act3",
    action: "viewed",
    itemTitle: "Tame Impala – Currents",
    category: "music",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
  },
  {
    id: "act4",
    action: "rated",
    itemTitle: "Attack on Titan",
    detail: "4",
    category: "anime",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString(),
  },
  {
    id: "act5",
    action: "added",
    itemTitle: "Dishoom King's Cross",
    category: "restaurant",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
  {
    id: "act6",
    action: "liked",
    itemTitle: "Radiohead – In Rainbows",
    category: "music",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 30).toISOString(),
  },
  {
    id: "act7",
    action: "rated",
    itemTitle: "Fullmetal Alchemist: Brotherhood",
    detail: "5",
    category: "anime",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
  },
]
