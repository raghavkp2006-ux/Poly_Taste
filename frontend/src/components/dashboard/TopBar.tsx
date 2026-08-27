import { cn } from "@/lib/utils"
import { Button } from "@/components/ui"
import { LogOut } from "lucide-react"
import { api } from "../../api"
import { ConnectionBadge } from "../interchange"
import { useTheme } from "../ui/ThemeProvider"
import { ThemeToggleButton } from "../ui/ThemeToggleButton"

interface TopBarProps {
  userName: string
  onLogout: () => void
  connections?: { spotify: boolean; anilist: boolean; location: boolean } | null
}

export function TopBar({ userName, onLogout, connections }: TopBarProps) {
  // Theme state lives in ThemeProvider at the root — just consume it
  useTheme() // ensures re-render when theme changes

  const displayName = userName
    ? (userName.includes("@") ? userName.split("@")[0] : userName.split(" ")[0]) || "You"
    : "You"
  const initial = displayName[0]?.toUpperCase() ?? "U"

  return (
    <header
      className={cn(
        "flex items-center justify-between gap-4 px-4 md:px-6 py-3",
        "border-b border-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out",
        "sticky top-0 z-30 bg-[#FFFFFF] dark:bg-[#18181B] transition-colors duration-150 ease-out"
      )}
    >
      <div className="flex items-center gap-3 min-w-0">
        <div className="relative h-9 w-9 shrink-0 rounded-full flex items-center justify-center border border-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out">
          <div className="h-full w-full rounded-full flex items-center justify-center text-sm font-semibold text-[#18181B] dark:text-[#FAFAFA] bg-[#FFFFFF] dark:bg-[#18181B] transition-colors duration-150 ease-out">
            {initial}
          </div>
        </div>

        <div className="min-w-0">
          <h1 className="text-sm font-medium truncate leading-tight font-sans text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out">
            Welcome back,{" "}
            <span className="font-semibold">
              {displayName}
            </span>
          </h1>
          <p className="text-xs hidden sm:block leading-tight mt-0.5 font-sans text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out">
            Your signal is live.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {connections && (
          <div className="flex items-center gap-2.5">
            <div
              onClick={() => {
                if (!connections.spotify) window.location.href = api.auth.loginUrl
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] tracking-wide uppercase border border-[#E4E4E7] dark:border-[#3F3F46] hover:border-[#D4D4D8] dark:hover:border-[#52525B] transition-colors duration-150 ease-out",
                !connections.spotify && "cursor-pointer hover:bg-[#FAFAFA] dark:hover:bg-[#27272A]",
                connections.spotify ? "text-[#2563EB] dark:text-[#3B82F6]" : "text-[#71717A] dark:text-[#A1A1AA]"
              )}
              title={connections.spotify ? "Spotify Connected" : "Connect Spotify"}
            >
              <ConnectionBadge connected={connections.spotify} domain="music" size={12} />
              <span>Spotify</span>
            </div>

            <div
              onClick={() => {
                if (!connections.anilist) window.location.href = api.anilist.loginUrl
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] tracking-wide uppercase border border-[#E4E4E7] dark:border-[#3F3F46] hover:border-[#D4D4D8] dark:hover:border-[#52525B] transition-colors duration-150 ease-out",
                !connections.anilist && "cursor-pointer hover:bg-[#FAFAFA] dark:hover:bg-[#27272A]",
                connections.anilist ? "text-[#2563EB] dark:text-[#3B82F6]" : "text-[#71717A] dark:text-[#A1A1AA]"
              )}
              title={connections.anilist ? "AniList Connected" : "Connect AniList"}
            >
              <ConnectionBadge connected={connections.anilist} domain="anime" size={12} />
              <span>AniList</span>
            </div>
          </div>
        )}

        <div className="flex items-center gap-1">
          {/* Theme toggle — uses shared context from ThemeProvider */}
          <ThemeToggleButton />

          <Button
            variant="ghost"
            size="icon"
            onClick={onLogout}
            className="hover:text-red-600 dark:hover:text-red-500 hover:bg-red-500/10 transition-colors duration-150 text-[#71717A] dark:text-[#A1A1AA] ease-out rounded-lg h-9 w-9"
            aria-label="Logout"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
