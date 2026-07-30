const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000"

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Unauthorized")
    }
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `API error: ${response.status}`)
  }

  return response.json()
}

export const api = {
  auth: {
    me: () => fetchApi<{ user_id: string }>("/auth/me"),
    login: (req: any) => fetchApi<{ message: string, user_id: string }>("/auth/login", { 
      method: "POST", 
      body: JSON.stringify(req) 
    }),
    logout: () => fetchApi<{ message: string }>("/auth/logout", { method: "POST" }),
    loginUrl: `${API_BASE}/spotify/login`,
    googleLoginUrl: `${API_BASE}/auth/google/login`,
    googleCallback: (id_token: string) =>
      fetchApi<{ message: string, user_id: string }>("/auth/google/callback", {
        method: "POST",
        body: JSON.stringify({ id_token }),
      }),
  },
  taste: {
    getProfile: () => fetchApi<any>("/taste-profile"),
  },
  anime: {
    getTop: () => fetchApi<any[]>("/anime/top"),
    search: (q: string) => fetchApi<any[]>(`/anime/search?q=${encodeURIComponent(q)}`),
    getUpcoming: () => fetchApi<any[]>("/anime/upcoming"),
    getDetail: (mal_id: number) => fetchApi<any>(`/anime/${mal_id}`),
    getReviews: (mal_id: number) => fetchApi<any[]>(`/anime/${mal_id}/reviews`),
    getVideos: (mal_id: number) => fetchApi<any[]>(`/anime/${mal_id}/videos`),
    getNews: (mal_id: number) => fetchApi<any[]>(`/anime/${mal_id}/news`),
    recommend: (mal_id: number, personalize: boolean = false) => 
      fetchApi<{ recommendations: any[], personalized: boolean }>(`/anime/${mal_id}/recommend?personalize=${personalize}`),
    getDashboardRecommendations: async () => {
      // Hardcoded liked_ids for demo purposes: One Piece (21), Bleach (269), Naruto Shippuuden (1735)
      const res = await fetchApi<{ recommendations: any[] }>("/anime/recommendations", {
        method: "POST",
        body: JSON.stringify({ liked_ids: ["21", "269", "1735"] })
      });
      return res.recommendations.map(r => ({
        ...r,
        id: String(r.id),
        score: Math.round(r.score * 100), // convert 0-1 score to 0-100% match
        category: "anime"
      })) as import("./types").Recommendation[];
    },
    like: (mal_id: number) => fetchApi("/anime/" + mal_id + "/like", { method: "POST" }),
    unlike: (mal_id: number) => fetchApi("/anime/" + mal_id + "/like", { method: "DELETE" }),
  },
  restaurants: {
    search: (q: string, lat?: number, lon?: number, location?: string) =>
      fetchApi<any>(`/restaurants/search?q=${encodeURIComponent(q)}&lat=${lat ?? ""}&lon=${lon ?? ""}&location=${encodeURIComponent(location || "")}`),
    getDetail: (place_id: string) => fetchApi<any>(`/restaurants/${place_id}`),
    recommend: (place_id: string, personalize: boolean = false) => 
      fetchApi<{ recommendations: any[], personalized: boolean }>(`/restaurants/${place_id}/recommend?personalize=${personalize}`),
    like: (place_id: string) => fetchApi(`/restaurants/${place_id}/like`, { method: "POST" }),
    unlike: (place_id: string) => fetchApi(`/restaurants/${place_id}/like`, { method: "DELETE" }),
  },
  recommendations: {
    getByCategory: (category: string) =>
      fetchApi<import("./types").Recommendation[]>(`/api/recommendations?category=${category}`),
    getRecent: () =>
      fetchApi<import("./types").RecentItem[]>("/api/recent"),
    getActivity: () =>
      fetchApi<import("./types").ActivityItem[]>("/api/activity"),
  },
}
