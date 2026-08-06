import { cn } from "@/lib/utils"
import { Button } from "@/components/ui"
import { LogOut } from "lucide-react"
import { useEffect } from "react"
import { api } from "../../api"
import { colors, domainColor, domainAlpha, fontFamily } from "../../tokens"
import { ConnectionBadge } from "../interchange"

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
        "border-b",
        "sticky top-0 z-30"
      )}
      style={{ backgroundColor: colors.paper, borderColor: "rgba(0,0,0,0.06)" }}
    >
      {/* Greeting section */}
      <div className="flex items-center gap-3 min-w-0">
        {/* Avatar — convergence gradient ring */}
        <div
          className="relative h-9 w-9 shrink-0 rounded-full flex items-center justify-center"
          style={{
            background: `linear-gradient(135deg, ${domainColor.music} 0%, #3ED6C4 100%)`,
            padding: "1.5px",
          }}
        >
          <div
            className="h-full w-full rounded-full flex items-center justify-center text-sm font-semibold"
            style={{ background: colors.paper, fontFamily: fontFamily.display, color: colors.ink }}
          >
            {initial}
          </div>
        </div>

        <div className="min-w-0">
          <h1 className="text-sm font-medium truncate leading-tight" style={{ fontFamily: fontFamily.body, color: colors.ink }}>
            Welcome back,{" "}
            <span className="font-semibold" style={{ fontFamily: fontFamily.display, color: domainColor.music }}>
              {displayName}
            </span>
          </h1>
          <p className="text-xs hidden sm:block leading-tight mt-0.5" style={{ fontFamily: fontFamily.body, color: colors.interchange }}>
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
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] tracking-wide uppercase border transition-all duration-200",
                !connections.spotify && "cursor-pointer hover:bg-black/5"
              )}
              style={{
                fontFamily: fontFamily.mono,
                borderColor: connections.spotify ? domainAlpha("music", 0.3) : "rgba(0,0,0,0.1)",
                backgroundColor: connections.spotify ? domainAlpha("music", 0.05) : "transparent",
                color: connections.spotify ? domainColor.music : colors.interchange
              }}
              title={connections.spotify ? "Spotify Connected" : "Connect Spotify"}
            >
              <ConnectionBadge connected={connections.spotify} domain="music" size={12} />
              <span>Spotify</span>
            </div>

            {/* AniList Badge */}
            <div
              onClick={() => {
                if (!connections.anilist) window.location.href = api.anilist.loginUrl
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] tracking-wide uppercase border transition-all duration-200",
                !connections.anilist && "cursor-pointer hover:bg-black/5"
              )}
              style={{
                fontFamily: fontFamily.mono,
                borderColor: connections.anilist ? domainAlpha("anime", 0.3) : "rgba(0,0,0,0.1)",
                backgroundColor: connections.anilist ? domainAlpha("anime", 0.05) : "transparent",
                color: connections.anilist ? domainColor.anime : colors.interchange
              }}
              title={connections.anilist ? "AniList Connected" : "Connect AniList"}
            >
              <ConnectionBadge connected={connections.anilist} domain="anime" size={12} />
              <span>AniList</span>
            </div>
          </div>
        )}

        <Button
          variant="ghost"
          size="icon"
          onClick={onLogout}
          className="hover:text-red-600 hover:bg-red-500/10 transition-colors"
          style={{ color: colors.interchange }}
          aria-label="Logout"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
