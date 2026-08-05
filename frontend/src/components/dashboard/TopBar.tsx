import { cn } from "@/lib/utils"
import { Button } from "@/components/ui"
import { LogOut } from "lucide-react"
import { useEffect } from "react"
import { api } from "../../api"

interface TopBarProps {
  userName: string
  onLogout: () => void
  connections?: { spotify: boolean; anilist: boolean; location: boolean } | null
}

export function TopBar({ userName, onLogout, connections }: TopBarProps) {
  // Force dark mode
  useEffect(() => {
    document.documentElement.classList.add("dark")
    localStorage.setItem("poly-theme", "dark")
  }, [])

  const displayName = userName
    ? (userName.includes("@") ? userName.split("@")[0] : userName.split(" ")[0]) || "You"
    : "You"
  const initial = displayName[0]?.toUpperCase() ?? "U"

  return (
    <header
      className={cn(
        "flex items-center justify-between gap-4 px-4 md:px-6 py-3",
        "border-b border-white/[0.06]",
        "sticky top-0 z-30",
        "glass-panel"
      )}
    >
      {/* Greeting section */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Avatar — convergence gradient ring */}
        <div
          className="relative h-9 w-9 shrink-0 rounded-full flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, #7C6CF0 0%, #3ED6C4 100%)",
            padding: "1.5px",
          }}
        >
          <div
            className="h-full w-full rounded-full flex items-center justify-center text-sm font-display font-semibold text-foreground"
            style={{ background: "#12181F" }}
          >
            {initial}
          </div>
        </div>

        <div className="min-w-0">
          <h1 className="text-sm font-sans font-medium truncate text-foreground leading-tight">
            Welcome back,{" "}
            <span className="font-display font-semibold text-gradient-convergence">
              {displayName}
            </span>
          </h1>
          <p className="text-xs text-muted-foreground hidden sm:block font-sans leading-tight mt-0.5">
            Your signal is live.
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {connections && (
          <div className="flex items-center gap-2.5">
            {/* Spotify Badge */}
            <div
              onClick={() => {
                if (!connections.spotify) window.location.href = api.auth.loginUrl
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] tracking-wide uppercase font-sans border transition-all duration-200",
                connections.spotify
                  ? "border-[#7C6CF0]/25 bg-[#7C6CF0]/5 text-[#7C6CF0]"
                  : "border-white/10 bg-transparent text-muted-foreground cursor-pointer hover:bg-white/5"
              )}
              title={connections.spotify ? "Spotify Connected" : "Connect Spotify"}
            >
              <div
                className="w-1 h-1 rounded-full shrink-0"
                style={{
                  backgroundColor: connections.spotify ? "#7C6CF0" : "rgba(255,255,255,0.3)",
                  boxShadow: connections.spotify ? "0 0 4px #7C6CF0" : "none"
                }}
              />
              <span>Spotify</span>
            </div>

            {/* AniList Badge */}
            <div
              onClick={() => {
                if (!connections.anilist) window.location.href = api.anilist.loginUrl
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] tracking-wide uppercase font-sans border transition-all duration-200",
                connections.anilist
                  ? "border-[#4A90E2]/25 bg-[#4A90E2]/5 text-[#4A90E2]"
                  : "border-white/10 bg-transparent text-muted-foreground cursor-pointer hover:bg-white/5"
              )}
              title={connections.anilist ? "AniList Connected" : "Connect AniList"}
            >
              <div
                className="w-1 h-1 rounded-full shrink-0"
                style={{
                  backgroundColor: connections.anilist ? "#4A90E2" : "rgba(255,255,255,0.3)",
                  boxShadow: connections.anilist ? "0 0 4px #4A90E2" : "none"
                }}
              />
              <span>AniList</span>
            </div>
          </div>
        )}

        <Button
          variant="ghost"
          size="icon"
          onClick={onLogout}
          className="text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
          aria-label="Logout"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
