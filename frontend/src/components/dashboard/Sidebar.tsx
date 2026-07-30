import { cn } from "@/lib/utils"
import {
  Home,
  Tv,
  UtensilsCrossed,
  Music,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import type { PageId } from "../../types"

interface NavItem {
  id: PageId
  label: string
  icon: React.ElementType
  color: string
}

const navItems: NavItem[] = [
  { id: "home", label: "Home", icon: Home, color: "#8A87A3" },
  { id: "anime", label: "Anime", icon: Tv, color: "#E8A23D" },
  { id: "restaurants", label: "Restaurants", icon: UtensilsCrossed, color: "#B23A2E" },
  { id: "music", label: "Music", icon: Music, color: "#C6318C" },
  { id: "settings", label: "Settings", icon: Settings, color: "#8A87A3" },
]

interface SidebarProps {
  currentPage: PageId
  onNavigate: (page: PageId) => void
  onLogout?: () => void
  collapsed: boolean
  onToggleCollapse: () => void
}

export function Sidebar({ currentPage, onNavigate, onLogout, collapsed, onToggleCollapse }: SidebarProps) {

  return (
    <>
      {/* Desktop sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={cn(
          "hidden md:flex flex-col fixed left-0 top-0 h-screen z-40",
          "border-r border-border/40"
        )}
        style={{ backgroundColor: "hsl(var(--sidebar))" }}
      >
        {/* Logo area */}
        <div className="flex items-center h-16 px-4 border-b border-border/40">
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.span
                key="logo-text"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="text-lg font-display tracking-wide truncate"
                style={{ color: "hsl(var(--sidebar-foreground))" }}
              >
                Poly_Taste
              </motion.span>
            )}
          </AnimatePresence>
          {collapsed && (
            <span
              className="text-lg font-display mx-auto"
              style={{ color: "hsl(var(--sidebar-foreground))" }}
            >
              P
            </span>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 py-4 space-y-1 px-3">
          {navItems.map((item) => {
            const isActive = currentPage === item.id
            const Icon = item.icon

            const button = (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={cn(
                  "relative flex items-center w-full rounded-none px-3 py-2.5 text-sm font-medium transition-colors duration-200",
                  "hover:bg-white/5",
                  isActive ? "font-semibold" : "font-normal"
                )}
                style={{
                  color: isActive ? item.color : "hsl(var(--sidebar-foreground))",
                }}
              >
                {/* Active indicator - left colored bar */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full"
                    style={{ backgroundColor: item.color }}
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon
                  className={cn(
                    "h-5 w-5 shrink-0 transition-colors"
                  )}
                  style={{ color: isActive ? item.color : "hsl(var(--sidebar-foreground))" }}
                />
                <AnimatePresence mode="wait">
                  {!collapsed && (
                    <motion.span
                      key={`label-${item.id}`}
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      className="ml-3 truncate font-body"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            )

            return collapsed ? (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className="flex items-center justify-center w-full rounded-none px-3 py-2.5 transition-colors duration-200 hover:bg-white/5"
                title={item.label}
              >
                <Icon
                  className="h-5 w-5"
                  style={{ color: isActive ? item.color : "hsl(var(--sidebar-foreground))" }}
                />
              </button>
            ) : (
              <div key={item.id}>{button}</div>
            )
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="p-3 border-t border-border/40">
          <button
            onClick={onToggleCollapse}
            className="flex items-center justify-center w-full rounded-none p-2 text-sidebar-foreground hover:bg-white/5 transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-2" />
                <span className="text-xs font-body font-medium">Collapse</span>
              </>
            )}
          </button>

          {onLogout && (
            <button
              onClick={onLogout}
              className="flex items-center justify-center w-full rounded-none p-2 mt-2 transition-colors hover:bg-brick-red/10"
              style={{ color: "#B23A2E" }}
            >
              {collapsed ? (
                <LogOut className="h-4 w-4" />
              ) : (
                <>
                  <LogOut className="h-4 w-4 mr-2" />
                  <span className="text-xs font-body font-medium">Logout</span>
                </>
              )}
            </button>
          )}
        </div>
      </motion.aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around h-16 border-t border-border/40 bg-sidebar/95 backdrop-blur-lg">
        {navItems.map((item) => {
          const isActive = currentPage === item.id
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                "flex flex-col items-center gap-0.5 py-1.5 px-3 rounded-none transition-colors relative",
                isActive ? "font-semibold" : "font-normal"
              )}
              style={{ color: isActive ? item.color : "hsl(var(--sidebar-foreground))" }}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-body">{item.label}</span>
              {isActive && (
                <motion.div
                  layoutId="mobile-active"
                  className="absolute -bottom-0 h-[2px] w-5 rounded-full"
                  style={{ backgroundColor: item.color }}
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
            </button>
          )
        })}
      </nav>
    </>
  )
}
