import { useState } from "react"
import { api } from "../../api"
import { Button } from "../ui"
import { domainColor, domainAlpha, fontFamily } from "../../tokens"
import type { Domain } from "../../tokens"
import { Card, ConnectionBadge } from "../interchange"
import { ThemeToggleButton } from "../ui/ThemeToggleButton"

// ── Step definitions ─────────────────────────────────────────────────

type StepId = "welcome" | "spotify" | "anilist" | "done"

const STEPS: StepId[] = ["welcome", "spotify", "anilist", "done"]

// ── Props ─────────────────────────────────────────────────────────────

interface OnboardingWizardProps {
  userId: string
  /** Which step index to start on (used for resume-after-redirect). */
  initialStep?: number
  onComplete: () => void
}

// ── Component ─────────────────────────────────────────────────────────

export function OnboardingWizard({
  userId,
  initialStep = 0,
  onComplete,
}: OnboardingWizardProps) {
  const [stepIndex, setStepIndex] = useState(
    Math.min(Math.max(initialStep, 0), STEPS.length - 1)
  )

  const step = STEPS[stepIndex]

  // ── Helpers ──────────────────────────────────────────────────────

  const advance = () => setStepIndex((i) => Math.min(i + 1, STEPS.length - 1))

  const finish = () => {
    localStorage.setItem(`onboarding_done_${userId}`, "true")
    onComplete()
  }

  const handleSkip = () => {
    advance()
  }

  const handleSpotifyConnect = () => {
    window.location.href = api.auth.loginUrl
  }

  const handleAniListConnect = () => {
    window.location.href = api.anilist.loginUrl
  }

  // ── Dot progress indicator ────────────────────────────────────────

  const stepDomains: (Domain | "neutral")[] = ["neutral", "music", "anime"]

  function ProgressDots() {
    return (
      <div className="flex items-center justify-center gap-3 mb-8">
        {STEPS.slice(0, -1).map((_, i) => {
          const domain = stepDomains[i]
          const isCurrent = i === stepIndex
          const isPast = i < stepIndex
          const isActive = isCurrent || isPast

          if (domain === "neutral") {
            return (
              <div key={i} className="relative flex items-center justify-center shrink-0" style={{ width: 14, height: 14 }}>
                 <svg viewBox="0 0 14 14" className="absolute inset-0">
                   <circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" className="text-black/15 dark:text-white/20" strokeWidth="2" />
                   {isActive && <circle cx="7" cy="7" r="5" fill="none" stroke="#8B87A8" strokeWidth="2" />}
                 </svg>
              </div>
            )
          }
          return (
            <ConnectionBadge 
              key={i} 
              connected={isActive} 
              domain={domain as Domain} 
              size={14} 
            />
          )
        })}
      </div>
    )
  }

  // ── Step renders ─────────────────────────────────────────────────

  function StepWelcome() {
    return (
      <>
        <div className="text-center space-y-3 mb-8">
          <h1 className="text-2xl font-bold text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.display }}>
            Welcome to Poly Taste
          </h1>
          <p className="text-sm max-w-sm mx-auto text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.body }}>
            We blend your music and anime signals into one unified taste model.
            Connecting these makes every recommendation more accurate.
          </p>
        </div>

        <div className="space-y-3 mb-8">
          {[
            { icon: "♪", label: "Spotify", desc: "Tune anime picks to your listening DNA" },
            { icon: "⬡", label: "AniList",  desc: "Seed your anime recommendations from your watch history" },
          ].map(({ icon, label, desc }) => (
            <div
              key={label}
              className="flex items-start gap-3 p-3 rounded-lg bg-black/[0.03] dark:bg-white/[0.03] border border-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out"
            >
              <span className="text-lg mt-0.5 text-[#8B87A8]">{icon}</span>
              <div>
                <p className="text-sm font-semibold text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.body }}>{label}</p>
                <p className="text-xs text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.body }}>{desc}</p>
              </div>
            </div>
          ))}
        </div>

        <Button
          id="btn-onboarding-start"
          className="w-full"
          onClick={advance}
        >
          Get Started
        </Button>
      </>
    )
  }

  function StepSpotify() {
    return (
      <>
        <div className="text-center space-y-2 mb-8">
          <div
            className="w-12 h-12 flex items-center justify-center rounded-full mx-auto mb-4"
            style={{ background: domainAlpha("music", 0.12), border: `1px solid ${domainAlpha("music", 0.25)}` }}
          >
            <span style={{ fontSize: 22, color: domainColor.music }}>♪</span>
          </div>
          <h2 className="text-xl font-bold text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.display }}>Connect Spotify</h2>
          <p className="text-sm max-w-xs mx-auto text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.body }}>
            We'll read your top tracks and artists to enrich recommendations across all domains.
            You can always connect later from your profile.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            id="btn-onboarding-spotify-connect"
            className="w-full"
            style={{ backgroundColor: domainColor.music, color: "#FFFFFF" }}
            onClick={handleSpotifyConnect}
          >
            Connect Spotify
          </Button>
          <button
            id="btn-onboarding-spotify-skip"
            className="w-full text-sm text-[#71717A] dark:text-[#A1A1AA] hover:text-[#18181B] dark:hover:text-[#FAFAFA] transition-colors py-2"
            style={{ fontFamily: fontFamily.body }}
            onClick={handleSkip}
          >
            Skip for now
          </button>
        </div>
      </>
    )
  }

  function StepAniList() {
    return (
      <>
        <div className="text-center space-y-2 mb-8">
          <div
            className="w-12 h-12 flex items-center justify-center rounded-full mx-auto mb-4"
            style={{ background: domainAlpha("anime", 0.12), border: `1px solid ${domainAlpha("anime", 0.25)}` }}
          >
            <span style={{ fontSize: 22, color: domainColor.anime }}>⬡</span>
          </div>
          <h2 className="text-xl font-bold text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.display }}>Connect AniList</h2>
          <p className="text-sm max-w-xs mx-auto text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.body }}>
            We'll import your watch history and ratings to instantly personalise anime
            recommendations. You can always connect later.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            id="btn-onboarding-anilist-connect"
            className="w-full"
            style={{ backgroundColor: domainColor.anime, color: "#FFFFFF" }}
            onClick={handleAniListConnect}
          >
            Connect AniList
          </Button>
          <button
            id="btn-onboarding-anilist-skip"
            className="w-full text-sm text-[#71717A] dark:text-[#A1A1AA] hover:text-[#18181B] dark:hover:text-[#FAFAFA] transition-colors py-2"
            style={{ fontFamily: fontFamily.body }}
            onClick={handleSkip}
          >
            Skip for now
          </button>
        </div>
      </>
    )
  }

  function StepDone() {
    return (
      <>
        <div className="text-center space-y-3 mb-8">
          <div
            className="w-12 h-12 flex items-center justify-center rounded-full mx-auto mb-4"
            style={{
              background:  "rgba(139,135,168,0.12)",
              border:      "1px solid rgba(139,135,168,0.25)",
            }}
          >
            <span className="text-xl font-bold text-[#18181B] dark:text-[#FAFAFA]">✓</span>
          </div>
          <h2 className="text-xl font-bold text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.display }}>You're all set!</h2>
          <p className="text-sm max-w-xs mx-auto text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out" style={{ fontFamily: fontFamily.body }}>
            Your Taste Passport is ready. Connect any remaining services from your profile
            page whenever you like.
          </p>
        </div>

        <Button
          id="btn-onboarding-finish"
          className="w-full"
          onClick={finish}
        >
          Go to Dashboard
        </Button>
      </>
    )
  }

  // ── Render ────────────────────────────────────────────────────────

  return (
    <div className="flex min-h-screen items-center justify-center p-4 relative">
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggleButton />
      </div>
      <Card
        className="w-full max-w-sm overflow-hidden"
      >
        <div className="p-8">
          {step !== "welcome" && step !== "done" && <ProgressDots />}

          {step === "welcome"  && <StepWelcome />}
          {step === "spotify"  && <StepSpotify />}
          {step === "anilist"  && <StepAniList />}
          {step === "done"     && <StepDone />}
        </div>
      </Card>
    </div>
  )
}
