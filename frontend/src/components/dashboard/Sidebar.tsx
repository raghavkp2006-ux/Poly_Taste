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
  Layers,
  Fingerprint,
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
  { id: "home",        label: "Home",        icon: Home,            color: "#A0AEC0" },
  { id: "anime",       label: "Anime",        icon: Tv,              color: "#FF7A59" },
  { id: "restaurants", label: "Food",         icon: UtensilsCrossed, color: "#E3A857" },
  { id: "music",       label: "Music",        icon: Music,           color: "#7C6CF0" },
  { id: "profile",     label: "Profile",      icon: Fingerprint,     color: "#3ED6C4" },
  { id: "settings",    label: "Settings",     icon: Settings,        color: "#A0AEC0" },
]

interface SidebarProps {
  currentPage: PageId
  onNavigate: (page: PageId) => void
  onLogout?: () => void
  collapsed: boolean
  onToggleCollapse: () => void
}

export function Sidebar({
  currentPage,
  onNavigate,
  onLogout,
  collapsed,
  onToggleCollapse,
}: SidebarProps) {
  return (
    <>
      {/* ── Desktop sidebar ─────────────────────────────────────── */}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={cn(
          "hidden md:flex flex-col fixed left-0 top-0 h-screen z-40",
          "glass-panel border-r border-white/[0.06]",
          "overflow-hidden"
        )}
      >
        {/* Logo area */}
        <div className="flex items-center h-16 px-4 border-b border-white/[0.06] shrink-0">
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.div
                key="logo-full"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="flex items-center gap-2.5 min-w-0"
              >
                <LogoMark size={28} />
                <span
                  className="text-base font-display font-semibold tracking-tight truncate text-foreground"
                >
                  Poly_Taste
                </span>
              </motion.div>
            )}
          </AnimatePresence>
          {collapsed && (
            <div className="mx-auto">
              <LogoMark size={28} />
            </div>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 py-4 space-y-0.5 px-3 overflow-y-auto scrollbar-hide">
          {navItems.map((item) => {
            const isActive = currentPage === item.id
            const Icon = item.icon

            return collapsed ? (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={cn(
                  "relative flex items-center justify-center w-full rounded-lg",
                  "h-10 transition-all duration-200",
                  "hover:bg-white/[0.06]",
                  isActive && "bg-white/[0.08]"
                )}
                title={item.label}
                aria-label={item.label}
              >
                <Icon
                  className="h-5 w-5 shrink-0 transition-colors"
                  style={{ color: isActive ? item.color : "#7B8794" }}
                />
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-collapsed"
                    className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full"
                    style={{ backgroundColor: item.color }}
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                {isActive && (
                  /* Glow halo behind icon */
                  <div
                    className="absolute inset-0 rounded-lg opacity-20"
                    style={{ backgroundColor: item.color }}
                  />
                )}
              </button>
            ) : (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={cn(
                  "relative flex items-center w-full rounded-lg px-3 py-2.5",
                  "text-sm font-sans transition-all duration-200",
                  "hover:bg-white/[0.06]",
                  isActive ? "bg-white/[0.08] font-medium" : "font-normal"
                )}
                style={{ color: isActive ? item.color : "#7B8794" }}
              >
                {/* Active left glow bar */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full"
                    style={{ backgroundColor: item.color, boxShadow: `0 0 8px ${item.color}80` }}
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                {/* Active bg glow */}
                {isActive && (
                  <div
                    className="absolute inset-0 rounded-lg opacity-10"
                    style={{ backgroundColor: item.color }}
                  />
                )}

                <Icon
                  className="h-5 w-5 shrink-0 relative z-10"
                  style={{ color: isActive ? item.color : "#7B8794" }}
                />
                <AnimatePresence mode="wait">
                  {!collapsed && (
                    <motion.span
                      key={`label-${item.id}`}
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      className="ml-3 truncate relative z-10 font-sans"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            )
          })}
        </nav>

        {/* Bottom controls */}
        <div className="p-3 border-t border-white/[0.06] space-y-1 shrink-0">
          {/* Collapse toggle */}
          <button
            onClick={onToggleCollapse}
            className={cn(
              "flex items-center w-full rounded-lg p-2",
              "text-muted-foreground hover:text-foreground",
              "hover:bg-white/[0.06] transition-all duration-200",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              collapsed ? "justify-center" : ""
            )}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-2" />
                <span className="text-xs font-sans">Collapse</span>
              </>
            )}
          </button>

          {/* Logout */}
          {onLogout && (
            <button
              onClick={onLogout}
              className={cn(
                "flex items-center w-full rounded-lg p-2",
                "text-muted-foreground",
                "hover:bg-red-500/10 hover:text-red-400",
                "transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                collapsed ? "justify-center" : ""
              )}
              aria-label="Logout"
            >
              {collapsed ? (
                <LogOut className="h-4 w-4" />
              ) : (
                <>
                  <LogOut className="h-4 w-4 mr-2" />
                  <span className="text-xs font-sans">Logout</span>
                </>
              )}
            </button>
          )}
        </div>
      </motion.aside>

      {/* ── Mobile bottom nav ─────────────────────────────────────── */}
      <nav
        className={cn(
          "md:hidden fixed bottom-0 left-0 right-0 z-40",
          "flex items-center justify-around h-16",
          "border-t border-white/[0.06]",
          "glass-panel"
        )}
      >
        {navItems.map((item) => {
          const isActive = currentPage === item.id
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                "relative flex flex-col items-center gap-0.5 py-2 px-3 rounded-lg",
                "transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              )}
              style={{ color: isActive ? item.color : "#7B8794" }}
              aria-label={item.label}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-sans font-medium">{item.label}</span>
              {isActive && (
                <motion.div
                  layoutId="mobile-active"
                  className="absolute -bottom-1 h-[2px] w-5 rounded-full"
                  style={{
                    backgroundColor: item.color,
                    boxShadow: `0 0 6px ${item.color}`,
                  }}
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

// ── Logo mark component ─────────────────────────────────────────────

function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: "linear-gradient(135deg, #7C6CF0 0%, #3ED6C4 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        boxShadow: "0 0 12px rgba(124,108,240,0.4)",
      }}
    >
      <Layers
        style={{
          width: size * 0.52,
          height: size * 0.52,
          color: "#ffffff",
          strokeWidth: 2.5,
        }}
      />
    </div>
  )
}
