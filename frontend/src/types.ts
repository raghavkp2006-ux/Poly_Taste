// ── Recommendation types ────────────────────────────────────────────

export type Category = "anime" | "restaurant" | "music"

export interface Recommendation {
  id: string
  title: string
  imageUrl: string
  reason: string
  /** Match score 0–100 */
  score: number
  category: Category
}

// ── Recently viewed ─────────────────────────────────────────────────

export interface RecentItem {
  id: string
  title: string
  imageUrl: string
  category: Category
  /** ISO timestamp of last view */
  viewedAt: string
}

// ── Activity feed ───────────────────────────────────────────────────

export type ActivityAction = "rated" | "liked" | "viewed" | "added"

export interface ActivityItem {
  id: string
  action: ActivityAction
  itemTitle: string
  /** e.g. "4" for a 4-star rating */
  detail?: string
  category: Category
  /** ISO timestamp */
  timestamp: string
}

// ── Navigation ──────────────────────────────────────────────────────

export type PageId = "home" | "anime" | "restaurants" | "music" | "profile" | "settings"
