"use client"

import { useState } from "react"
import { api } from "@/api"
import { AmbientBackground } from "./AmbientBackground"
import { fontFamily, domainColor } from "../../tokens"
import { Card } from "../interchange"
import { ThemeToggleButton } from "./ThemeToggleButton"

function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error,     setError]     = useState("")

  const handleGoogleLogin = () => {
    setError("")
    setIsLoading(true)
    window.location.href = api.auth.googleLoginUrl
  }

  const handleSkip = () => {
    api.auth
      .login({ email: "guest@poly.taste", password: "guest_password" })
      .catch(() => {})
      .finally(() => window.location.reload())
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden bg-[#FAFAFA] dark:bg-[#0A0A0B] text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out"
      style={{ fontFamily: fontFamily.body }}
    >
      <AmbientBackground />

      {/* Theme toggle in top right */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggleButton />
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-sm mx-auto text-center space-y-10">

        {/* Brand */}
        <div className="space-y-4">
          {/* Convergence ring logo */}
          <div className="mx-auto flex items-center justify-center" style={{ width: 56, height: 56 }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #7C6CF0 0%, #3ED6C4 100%)",
                padding: 2,
                boxShadow: "0 0 24px rgba(124,108,240,0.5), 0 0 48px rgba(62,214,196,0.2)",
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  borderRadius: "50%",
                  background: "#0A0E14",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <span
                  style={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontWeight: 700,
                    fontSize: 18,
                    background: "linear-gradient(135deg, #7C6CF0, #3ED6C4)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  P
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <h1
              className="text-3xl font-display font-bold tracking-tight text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out"
              style={{ fontFamily: fontFamily.display }}
            >
              Poly_Taste
            </h1>
            <p
              className="text-sm font-sans text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out"
              style={{ fontFamily: fontFamily.body }}
            >
              Your taste, unified.
            </p>
          </div>
          
          {/* Domain pills */}
          <div className="flex items-center justify-center gap-2 pt-1">
            <Pill color={domainColor.music} label="Music"  />
            <Pill color={domainColor.anime} label="Anime"  />
          </div>
        </div>

        {/* Auth card */}
        <Card className="space-y-4 p-6">
          {/* Google sign-in */}
          <button
            id="btn-google-login"
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 h-12 px-6 rounded-xl border border-[#E4E4E7] dark:border-[#27272A] bg-white dark:bg-[#18181B] text-[#18181B] dark:text-[#FAFAFA] hover:bg-[#F4F4F5] dark:hover:bg-[#27272A] shadow-sm dark:shadow-none transition-all duration-200 hover:scale-[1.01] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] dark:focus-visible:ring-[#3B82F6]"
          >
            {/* Google G */}
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.19 3.32v2.77h3.55c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-1 7.28-2.69l-3.55-2.77c-.99.66-2.25 1.06-3.73 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.72 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.72 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            <span className="text-sm font-sans font-semibold text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out">
              {isLoading ? "Signing in…" : "Continue with Google"}
            </span>
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out" />
            <span className="text-[10px] font-mono text-[#71717A] dark:text-[#A1A1AA] uppercase tracking-widest">or</span>
            <div className="flex-1 h-px bg-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out" />
          </div>

          {/* Skip */}
          <button
            id="btn-skip-login"
            onClick={handleSkip}
            className="w-full flex items-center justify-center h-10 text-sm font-sans rounded-xl text-[#71717A] dark:text-[#A1A1AA] hover:text-[#18181B] dark:hover:text-[#FAFAFA] transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] dark:focus-visible:ring-[#3B82F6]"
          >
            Skip for now — browse anime
          </button>
        </Card>

        {/* Error */}
        {error && (
          <p
            className="text-xs font-mono"
            style={{ color: "#FF7A59" }}
          >
            {error}
          </p>
        )}

        {/* Footer */}
        <div
          className="text-[9px] font-mono uppercase tracking-[0.2em] text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out"
        >
          Poly_Taste · Signal v2
        </div>
      </div>
    </div>
  )
}

function Pill({ color, label }: { color: string; label: string }) {
  return (
    <span
      className="text-[9px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full"
      style={{
        color,
        backgroundColor: `${color}12`,
        border: `1px solid ${color}25`,
      }}
    >
      {label}
    </span>
  )
}

export const Component = LoginPage
