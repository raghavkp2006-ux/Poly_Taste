import { cn } from "@/lib/utils"
import { Button } from "@/components/ui"
import { LogOut } from "lucide-react"
import { useEffect } from "react"

interface TopBarProps {
  userName: string
  onLogout: () => void
}

export function TopBar({ userName, onLogout }: TopBarProps) {
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
      <div className="flex items-center gap-2">
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
