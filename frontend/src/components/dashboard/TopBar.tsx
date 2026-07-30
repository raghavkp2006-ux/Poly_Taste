import { cn } from "@/lib/utils"
import { Button } from "@/components/ui"
import { LogOut } from "lucide-react"
import { useEffect } from "react"

interface TopBarProps {
  userName: string
  onLogout: () => void
}

export function TopBar({ userName, onLogout }: TopBarProps) {
  useEffect(() => {
    document.documentElement.classList.add("dark")
    localStorage.setItem("poly-theme", "dark")
  }, [])

  const firstName = userName.split(" ")[0]

  return (
    <header
      className={cn(
        "flex items-center justify-between gap-4 px-4 md:px-6 py-3",
        "border-b border-border/40 sticky top-0 z-30"
      )}
      style={{ backgroundColor: "hsl(var(--sidebar))" }}
    >
      {/* Greeting */}
      <div className="flex items-center gap-3 min-w-0">
        <div
          className="w-9 h-9 shrink-0 flex items-center justify-center font-display text-sm tracking-wide"
          style={{ backgroundColor: "hsl(var(--sidebar-accent))", color: "hsl(var(--sidebar-foreground))" }}
        >
          {firstName[0]?.toUpperCase() ?? "U"}
        </div>
        <div className="min-w-0">
          <h1 className="text-base font-body font-semibold truncate">
            <span className="text-foreground">Welcome back,</span>{" "}
            <span
              className="font-display tracking-wide"
              style={{ color: "hsl(var(--sidebar-accent))" }}
            >
              {firstName}
            </span>
          </h1>
          <p className="text-xs text-muted-foreground hidden sm:block font-body">
            Your passport is stamped — dive in.
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onLogout}
          className="rounded-none text-muted-foreground hover:text-brick-red transition-colors"
          aria-label="Logout"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
