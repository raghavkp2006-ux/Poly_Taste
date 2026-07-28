import { cn } from "@/lib/utils"
import { Input, Avatar, AvatarFallback, Button } from "@/components/ui"
import { Search, Moon, Sun, LogOut } from "lucide-react"
import { useEffect, useState } from "react"

interface TopBarProps {
  userName: string
  onLogout: () => void
}

export function TopBar({ userName, onLogout }: TopBarProps) {
  const [dark, setDark] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("poly-theme") === "dark"
    }
    return false
  })
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    const root = document.documentElement
    if (dark) {
      root.classList.add("dark")
      localStorage.setItem("poly-theme", "dark")
    } else {
      root.classList.remove("dark")
      localStorage.setItem("poly-theme", "light")
    }
  }, [dark])

  // Also apply on mount if preference was saved
  useEffect(() => {
    const saved = localStorage.getItem("poly-theme")
    if (saved === "dark") {
      document.documentElement.classList.add("dark")
      setDark(true)
    }
  }, [])

  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  const firstName = userName.split(" ")[0]

  return (
    <header
      className={cn(
        "flex items-center justify-between gap-4 px-6 py-4",
        "bg-background/80 backdrop-blur-md sticky top-0 z-30",
        "border-b border-border"
      )}
    >
      {/* Greeting */}
      <div className="flex items-center gap-3 min-w-0">
        <Avatar className="h-10 w-10 hidden sm:flex">
          <AvatarFallback>{initials || "U"}</AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <h1 className="text-lg font-semibold truncate">
            Welcome back,{" "}
            <span className="bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
              {firstName}
            </span>
          </h1>
          <p className="text-xs text-muted-foreground hidden sm:block">
            Here's what we've picked for you today
          </p>
        </div>
      </div>

      {/* Search + Actions */}
      <div className="flex items-center gap-2">
        <div className="relative hidden sm:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search recommendations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 w-56 lg:w-72 bg-muted/50 border-0 focus-visible:ring-1"
          />
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setDark(!dark)}
          className="rounded-full"
          aria-label="Toggle dark mode"
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onLogout}
          className="rounded-full text-muted-foreground hover:text-destructive"
          aria-label="Logout"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
