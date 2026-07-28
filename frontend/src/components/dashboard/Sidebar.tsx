import { cn } from "@/lib/utils"
import { Tooltip } from "@/components/ui"
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
import { useState } from "react"
import type { PageId } from "../../types"

interface NavItem {
  id: PageId
  label: string
  icon: React.ElementType
}

const navItems: NavItem[] = [
  { id: "home", label: "Home", icon: Home },
  { id: "anime", label: "Anime", icon: Tv },
  { id: "restaurants", label: "Restaurants", icon: UtensilsCrossed },
  { id: "music", label: "Music", icon: Music },
  { id: "settings", label: "Settings", icon: Settings },
]

interface SidebarProps {
  currentPage: PageId
  onNavigate: (page: PageId) => void
  onLogout?: () => void
}

export function Sidebar({ currentPage, onNavigate, onLogout }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <>
      {/* Desktop sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={cn(
          "hidden md:flex flex-col fixed left-0 top-0 h-screen z-40",
          "bg-sidebar border-r border-border"
        )}
      >
        {/* Logo area */}
        <div className="flex items-center h-16 px-4 border-b border-border">
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.span
                key="logo-text"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="text-lg font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent truncate"
              >
                Poly_Taste
              </motion.span>
            )}
          </AnimatePresence>
          {collapsed && (
            <span className="text-lg font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent mx-auto">
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
                  "relative flex items-center w-full rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  "hover:bg-accent/60",
                  isActive
                    ? "text-primary bg-primary/10"
                    : "text-sidebar-foreground"
                )}
              >
                {/* Active indicator pill */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full bg-primary"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon
                  className={cn(
                    "h-5 w-5 shrink-0 transition-colors",
                    isActive ? "text-primary" : "text-sidebar-foreground"
                  )}
                />
                <AnimatePresence mode="wait">
                  {!collapsed && (
                    <motion.span
                      key={`label-${item.id}`}
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      className="ml-3 truncate"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            )

            return collapsed ? (
              <Tooltip key={item.id} content={item.label}>
                {button}
              </Tooltip>
            ) : (
              <div key={item.id}>{button}</div>
            )
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="p-3 border-t border-border">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-center w-full rounded-lg p-2 text-sidebar-foreground hover:bg-accent/60 transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-2" />
                <span className="text-xs font-medium">Collapse</span>
              </>
            )}
          </button>
          
          {onLogout && (
            <button
              onClick={onLogout}
              className="flex items-center justify-center w-full rounded-lg p-2 mt-2 text-destructive hover:bg-destructive/10 transition-colors"
            >
              {collapsed ? (
                <Tooltip content="Logout">
                  <LogOut className="h-4 w-4" />
                </Tooltip>
              ) : (
                <>
                  <LogOut className="h-4 w-4 mr-2" />
                  <span className="text-xs font-medium">Logout</span>
                </>
              )}
            </button>
          )}
        </div>
      </motion.aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around h-16 bg-sidebar border-t border-border backdrop-blur-lg bg-opacity-95">
        {navItems.map((item) => {
          const isActive = currentPage === item.id
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                "flex flex-col items-center gap-0.5 py-1.5 px-3 rounded-lg transition-colors",
                isActive ? "text-primary" : "text-sidebar-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
              {isActive && (
                <motion.div
                  layoutId="mobile-active"
                  className="absolute -bottom-0 h-0.5 w-8 rounded-full bg-primary"
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
