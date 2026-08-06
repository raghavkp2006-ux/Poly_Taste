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
import { api } from "../../api"
import { colors, domainColor, domainAlpha, fontFamily } from "../../tokens"
import type { Domain } from "../../tokens"
import { ConnectionBadge } from "../interchange"

interface NavItem {
  id: PageId
  label: string
  icon: React.ElementType
  color: string
}

const navItems: NavItem[] = [
  { id: "home",        label: "Home",        icon: Home,            color: colors.interchange },
  { id: "anime",       label: "Anime",        icon: Tv,              color: domainColor.anime },
  { id: "restaurants", label: "Food",         icon: UtensilsCrossed, color: domainColor.food },
  { id: "music",       label: "Music",        icon: Music,           color: domainColor.music },
  { id: "profile",     label: "Profile",      icon: Fingerprint,     color: "#3ED6C4" },
  { id: "settings",    label: "Settings",     icon: Settings,        color: colors.interchange },
]

interface SidebarProps {
  currentPage: PageId
  onNavigate: (page: PageId) => void
  onLogout?: () => void
  collapsed: boolean
  onToggleCollapse: () => void
  connections?: { spotify: boolean; anilist: boolean; location: boolean } | null
}

function ConnectionItem({
  label,
  connected,
  color,
  onClick
  label: string
  connected: boolean
  color: string
  domain: Domain
  onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "flex items-center justify-between p-1.5 rounded-lg text-xs transition-all duration-200",
        !connected && "cursor-pointer hover:bg-black/5"
      )}
      style={{ fontFamily: fontFamily.body }}
    >
      <div className="flex items-center gap-2">
        <ConnectionBadge connected={connected} domain={domain} size={14} />
        <span style={{ color: connected ? colors.ink : colors.interchange, fontWeight: connected ? 500 : 400 }}>
          {label}
        </span>
      </div>
      <span
        className="text-[9px] uppercase tracking-wider"
        style={{ fontFamily: fontFamily.mono, color: connected ? color : colors.interchange }}
      >
        {connected ? "Connected" : "Connect"}
      </span>
    </div>
  )
}

export function Sidebar({
  currentPage,
  onNavigate,
  onLogout,
  collapsed,
  onToggleCollapse,
  connections,
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
          "border-r",
          "overflow-hidden"
        )}
        style={{ backgroundColor: colors.paper, borderColor: "rgba(0,0,0,0.06)" }}
      >
        {/* Logo area */}
        <div className="flex items-center h-16 px-4 border-b shrink-0" style={{ borderColor: "rgba(0,0,0,0.06)" }}>
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
                  className="text-base font-semibold tracking-tight truncate"
                  style={{ fontFamily: fontFamily.display, color: colors.ink }}
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
                  "hover:bg-black/5",
                  isActive && "bg-black/5"
                )}
                title={item.label}
                aria-label={item.label}
              >
                <Icon
                  className="h-5 w-5 shrink-0 transition-colors"
                  style={{ color: isActive ? item.color : colors.interchange }}
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
                    className="absolute inset-0 rounded-lg opacity-10"
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
                  "text-sm transition-all duration-200",
                  "hover:bg-black/5",
                  isActive ? "bg-black/5 font-medium" : "font-normal"
                )}
                style={{ fontFamily: fontFamily.body, color: isActive ? item.color : colors.interchange }}
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
                    className="absolute inset-0 rounded-lg opacity-5"
                    style={{ backgroundColor: item.color }}
                  />
                )}

                <Icon
                  className="h-5 w-5 shrink-0 relative z-10"
                  style={{ color: isActive ? item.color : colors.interchange }}
                />
                <AnimatePresence mode="wait">
                  {!collapsed && (
                    <motion.span
                      key={`label-${item.id}`}
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      className="ml-3 truncate relative z-10"
                      style={{ color: isActive ? colors.ink : colors.interchange }}
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            )
          })}
        </nav>

        {/* Connection status indicators */}
        {connections && (
          !collapsed ? (
            <div className="px-4 py-3 border-t space-y-2 shrink-0" style={{ borderColor: "rgba(0,0,0,0.06)" }}>
              <div 
                className="text-[10px] font-semibold uppercase tracking-wider"
                style={{ fontFamily: fontFamily.display, color: colors.interchange }}
              >
                Connections
              </div>
              <div className="flex flex-col gap-1">
                <ConnectionItem
                  label="Spotify"
                  connected={connections.spotify}
                  color={domainColor.music}
                  domain="music"
                  onClick={() => {
                    if (!connections.spotify) window.location.href = api.auth.loginUrl
                  }}
                />
                <ConnectionItem
                  label="AniList"
                  connected={connections.anilist}
                  color={domainColor.anime}
                  domain="anime"
                  onClick={() => {
                    if (!connections.anilist) window.location.href = api.anilist.loginUrl
                  }}
                />
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 py-3 border-t shrink-0" style={{ borderColor: "rgba(0,0,0,0.06)" }}>
              <div
                className="cursor-pointer"
                onClick={() => {
                  if (!connections.spotify) window.location.href = api.auth.loginUrl
                }}
                title={`Spotify: ${connections.spotify ? "Connected" : "Not connected (Click to connect)"}`}
              >
                <ConnectionBadge connected={connections.spotify} domain="music" size={24} letter="S" />
              </div>
              <div
                className="cursor-pointer"
                onClick={() => {
                  if (!connections.anilist) window.location.href = api.anilist.loginUrl
                }}
                title={`AniList: ${connections.anilist ? "Connected" : "Not connected (Click to connect)"}`}
              >
                <ConnectionBadge connected={connections.anilist} domain="anime" size={24} letter="A" />
              </div>
            </div>
          )
        )}

        {/* Bottom controls */}
        <div className="p-3 border-t space-y-1 shrink-0" style={{ borderColor: "rgba(0,0,0,0.06)" }}>
          {/* Collapse toggle */}
          <button
            onClick={onToggleCollapse}
            className={cn(
              "flex items-center w-full rounded-lg p-2",
              "hover:bg-black/5 transition-all duration-200",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              collapsed ? "justify-center" : ""
            )}
            style={{ color: colors.interchange }}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-2" />
                <span className="text-xs" style={{ fontFamily: fontFamily.body }}>Collapse</span>
              </>
            )}
          </button>

          {/* Logout */}
          {onLogout && (
            <button
              onClick={onLogout}
              className={cn(
                "flex items-center w-full rounded-lg p-2",
                "hover:bg-red-500/10 hover:text-red-600",
                "transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                collapsed ? "justify-center" : ""
              )}
              style={{ color: colors.interchange }}
              aria-label="Logout"
            >
              {collapsed ? (
                <LogOut className="h-4 w-4" />
              ) : (
                <>
                  <LogOut className="h-4 w-4 mr-2" />
                  <span className="text-xs" style={{ fontFamily: fontFamily.body }}>Logout</span>
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
          "border-t"
        )}
        style={{ backgroundColor: colors.paper, borderColor: "rgba(0,0,0,0.06)" }}
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
              style={{ color: isActive ? item.color : colors.interchange }}
              aria-label={item.label}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-medium" style={{ fontFamily: fontFamily.body, color: isActive ? colors.ink : colors.interchange }}>{item.label}</span>
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
        background: `linear-gradient(135deg, ${domainColor.music} 0%, #3ED6C4 100%)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        boxShadow: `0 0 12px ${domainAlpha("music", 0.4)}`,
      }}
    >
      <Layers
        style={{
          width: size * 0.52,
          height: size * 0.52,
          color: colors.paper,
          strokeWidth: 2.5,
        }}
      />
    </div>
  )
}
