/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Domain accent raw values (used as glows / borders only) ────────
        "music-accent": "#7C6CF0",
        "anime-accent": "#FF7A59",
        "food-accent":  "#E3A857",
        "convergence-from": "#7C6CF0",
        "convergence-to":   "#3ED6C4",

        // ── Graphite base ───────────────────────────────────────────────────
        graphite: {
          DEFAULT: "#0A0E14",
          panel:   "#12181F",
          rail:    "#0D1117",
        },

        // ── Semantic tokens (via CSS vars) — read by shadcn components ──────
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar))",
          foreground: "hsl(var(--sidebar-foreground))",
          accent: "hsl(var(--sidebar-accent))",
        },
        // Domain semantic (for Tailwind class usage)
        anime:       "hsl(var(--color-anime))",
        music:       "hsl(var(--color-music))",
        food:        "hsl(var(--color-food))",
        convergence: "hsl(var(--color-convergence))",
        border: "hsl(var(--border))",
        input:  "hsl(var(--input))",
        ring:   "hsl(var(--ring))",
      },

      borderRadius: {
        none: "0",
        sm:   "0.375rem",
        DEFAULT: "0.5rem",
        md:   "0.625rem",
        lg:   "0.75rem",
        xl:   "1rem",
        "2xl": "1.25rem",
        full: "9999px",
      },

      fontFamily: {
        // Display headers (Interchange: Fraunces; legacy fallback: Space Grotesk)
        display: ["Fraunces", "Space Grotesk", "Georgia", "serif"],
        // Body copy
        sans:    ["Inter", "system-ui", "sans-serif"],
        // Scores / metadata
        mono:    ["JetBrains Mono", "monospace"],
      },

      keyframes: {
        // Ambient background sphere drift
        "drift-a": {
          "0%":   { transform: "translate(0, 0) scale(1)" },
          "33%":  { transform: "translate(4%, 6%) scale(1.06)" },
          "66%":  { transform: "translate(-3%, 2%) scale(0.97)" },
          "100%": { transform: "translate(0, 0) scale(1)" },
        },
        "drift-b": {
          "0%":   { transform: "translate(0, 0) scale(1)" },
          "40%":  { transform: "translate(-5%, -4%) scale(1.08)" },
          "80%":  { transform: "translate(3%, 5%) scale(0.95)" },
          "100%": { transform: "translate(0, 0) scale(1)" },
        },
        "drift-c": {
          "0%":   { transform: "translate(0, 0) scale(1)" },
          "50%":  { transform: "translate(6%, -3%) scale(1.04)" },
          "100%": { transform: "translate(0, 0) scale(1)" },
        },
        // Halo convergence
        "halo-drift-music": {
          "0%":   { transform: "translate(-20px, -15px)", opacity: "0.7" },
          "50%":  { transform: "translate(-8px, -5px)",  opacity: "1" },
          "100%": { transform: "translate(0, 0)",        opacity: "1" },
        },
        "halo-drift-anime": {
          "0%":   { transform: "translate(20px, -15px)", opacity: "0.7" },
          "50%":  { transform: "translate(8px, -5px)",  opacity: "1" },
          "100%": { transform: "translate(0, 0)",        opacity: "1" },
        },
        "halo-drift-food": {
          "0%":   { transform: "translate(0, 25px)", opacity: "0.7" },
          "50%":  { transform: "translate(0, 10px)", opacity: "1" },
          "100%": { transform: "translate(0, 0)",     opacity: "1" },
        },
        "halo-spin": {
          from: { transform: "rotate(0deg)" },
          to:   { transform: "rotate(360deg)" },
        },
        // Card signal-in entrance
        "signal-in": {
          "0%":   { opacity: "0", transform: "translateY(16px) scale(0.96)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        // Generic fade-up
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        // Glow pulse for active indicators
        "glow-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.5" },
        },
        // Gradient shimmer for skeletons
        gradient: {
          to: { backgroundPosition: "200% center" },
        },
        // Score ring dash animation
        "ring-draw": {
          from: { strokeDashoffset: "var(--ring-circumference)" },
          to:   { strokeDashoffset: "var(--ring-dashoffset)" },
        },
      },

      animation: {
        "drift-a":       "drift-a 28s ease-in-out infinite",
        "drift-b":       "drift-b 36s ease-in-out infinite reverse",
        "drift-c":       "drift-c 22s ease-in-out infinite",
        "halo-spin":     "halo-spin 12s linear infinite",
        "signal-in":     "signal-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards",
        "fade-up":       "fade-up 0.4s ease-out forwards",
        "glow-pulse":    "glow-pulse 2s ease-in-out infinite",
        gradient:        "gradient 8s linear infinite",
        "ring-draw":     "ring-draw 1s ease-out forwards",
      },

      backdropBlur: {
        xs: "2px",
      },

      backgroundSize: {
        "200%": "200%",
      },
    },
  },
  plugins: [],
}
