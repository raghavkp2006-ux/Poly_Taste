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
        // ── Palette ──────────────────────────────────────────────────
        ink: {
          DEFAULT: "#10262A",
          light: "#1B3A42",
          lighter: "#2A4F59",
        },
        parchment: {
          DEFAULT: "#EFE6D8",
          dark: "#D9CEBC",
        },
        "stage-magenta": "#C6318C",
        "cel-amber": "#E8A23D",
        "brick-red": "#B23A2E",

        // ── Semantic tokens (via CSS vars) ──────────────────────────
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
        anime: "hsl(var(--color-anime))",
        music: "hsl(var(--color-music))",
        food: "hsl(var(--color-food))",
        convergence: "hsl(var(--color-convergence))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
      borderRadius: {
        none: "0",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Fraunces", "Georgia", "serif"],
        display: ["Archivo Black", "Impact", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      keyframes: {
        "stamp-in": {
          "0%": { opacity: "0", transform: "scale(2.4) rotate(-14deg)" },
          "55%": { opacity: "1", transform: "scale(0.92) rotate(1.5deg)" },
          "100%": { opacity: "1", transform: "scale(1) rotate(-3deg)" },
        },
        "ticket-enter": {
          "0%": { opacity: "0", transform: "translateY(10px) scale(0.97)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        gradient: {
          to: { backgroundPosition: "200% center" },
        },
      },
      animation: {
        "stamp-in": "stamp-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) both",
        "ticket-enter": "ticket-enter 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
        "fade-in": "fade-in 0.4s ease-out forwards",
        gradient: "gradient 8s linear infinite",
      },
    },
  },
  plugins: [],
}
