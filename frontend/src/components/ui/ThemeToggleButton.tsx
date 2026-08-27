import { Sun, Moon } from "lucide-react"
import { useTheme } from "./ThemeProvider"
import { cn } from "@/lib/utils"

interface ThemeToggleButtonProps {
  className?: string
}

export function ThemeToggleButton({ className }: ThemeToggleButtonProps) {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
      className={cn(
        "relative inline-flex items-center justify-center",
        "h-9 w-9 rounded-lg",
        "border border-[#E4E4E7] dark:border-[#27272A]",
        "bg-white dark:bg-[#18181B]",
        "text-[#18181B] dark:text-[#FAFAFA]",
        "hover:bg-[#F4F4F5] dark:hover:bg-[#27272A]",
        "transition-all duration-150 ease-out",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] dark:focus-visible:ring-[#3B82F6]",
        "shadow-sm dark:shadow-none",
        className
      )}
    >
      {/* Sun icon slides in from bottom in dark mode, out in light */}
      <span
        className={cn(
          "absolute transition-all duration-200",
          theme === "dark" ? "opacity-100 scale-100 rotate-0" : "opacity-0 scale-75 rotate-90"
        )}
      >
        <Sun className="h-4 w-4" />
      </span>
      {/* Moon icon visible in light mode */}
      <span
        className={cn(
          "absolute transition-all duration-200",
          theme === "light" ? "opacity-100 scale-100 rotate-0" : "opacity-0 scale-75 -rotate-90"
        )}
      >
        <Moon className="h-4 w-4" />
      </span>
    </button>
  )
}
