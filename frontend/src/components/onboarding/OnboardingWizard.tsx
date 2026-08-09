import { useState } from "react"
import { api } from "../../api"
import { Button } from "../ui"
import { colors, domainColor, domainAlpha, fontFamily } from "../../tokens"
import type { Domain } from "../../tokens"
import { Card, ConnectionBadge } from "../interchange"

// ── Step definitions ─────────────────────────────────────────────────

type StepId = "welcome" | "spotify" | "anilist" | "location" | "done"

const STEPS: StepId[] = ["welcome", "spotify", "anilist", "location", "done"]

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
  const [locationStatus, setLocationStatus] = useState<
    "idle" | "requesting" | "granted" | "denied"
  >("idle")

  const step = STEPS[stepIndex]

  // ── Helpers ──────────────────────────────────────────────────────

  const advance = () => setStepIndex((i) => Math.min(i + 1, STEPS.length - 1))

  const finish = () => {
    localStorage.setItem(`onboarding_done_${userId}`, "true")
    onComplete()
  }

  const handleSkip = () => {
    if (stepIndex >= STEPS.length - 2) {
      // On the last optional step (location), skip → done step
      advance()
    } else {
      advance()
    }
  }

  const handleSpotifyConnect = () => {
    window.location.href = api.auth.loginUrl
  }

  const handleAniListConnect = () => {
    window.location.href = api.anilist.loginUrl
  }

  const handleLocationRequest = () => {
    if (!navigator.geolocation) {
      advance()
      return
    }
    setLocationStatus("requesting")
    navigator.geolocation.getCurrentPosition(
      () => {
        setLocationStatus("granted")
        // Auto-advance after brief acknowledgement
        setTimeout(advance, 900)
      },
      () => {
        setLocationStatus("denied")
        setTimeout(advance, 900)
      },
      { timeout: 10000, maximumAge: 300000 }
    )
  }

  // ── Dot progress indicator ────────────────────────────────────────

  const stepDomains: (Domain | "neutral")[] = ["neutral", "music", "anime", "neutral"]

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
                   <circle cx="7" cy="7" r="5" fill="none" stroke={colors.ink} strokeOpacity={0.08} strokeWidth="2" />
                   {isActive && <circle cx="7" cy="7" r="5" fill="none" stroke={colors.interchange} strokeWidth="2" />}
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
          <h1 className="text-2xl font-bold" style={{ fontFamily: fontFamily.display, color: colors.ink }}>
            Welcome to Poly Taste
          </h1>
          <p className="text-sm max-w-sm mx-auto" style={{ fontFamily: fontFamily.body, color: colors.interchange }}>
            We blend your music, anime, and location signals into one unified taste model.
            Connecting these makes every recommendation more accurate.
          </p>
        </div>

        <div className="space-y-3 mb-8">
          {[
            { icon: "♪", label: "Spotify", desc: "Tune anime & restaurant picks to your listening DNA" },
            { icon: "⬡", label: "AniList",  desc: "Seed your anime recommendations from your watch history" },
            { icon: "⊙", label: "Location", desc: "Find restaurants near you, personalised to your vibe" },
          ].map(({ icon, label, desc }) => (
            <div
              key={label}
              className="flex items-start gap-3 p-3 rounded-lg"
              style={{ background: "rgba(0,0,0,0.02)", border: "1px solid rgba(0,0,0,0.05)" }}
            >
              <span className="text-lg mt-0.5" style={{ color: colors.interchange }}>{icon}</span>
              <div>
                <p className="text-sm font-semibold" style={{ fontFamily: fontFamily.body, color: colors.ink }}>{label}</p>
                <p className="text-xs" style={{ fontFamily: fontFamily.body, color: colors.interchange }}>{desc}</p>
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
          <h2 className="text-xl font-bold" style={{ fontFamily: fontFamily.display, color: colors.ink }}>Connect Spotify</h2>
          <p className="text-sm max-w-xs mx-auto" style={{ fontFamily: fontFamily.body, color: colors.interchange }}>
            We'll read your top tracks and artists to enrich recommendations across all domains.
            You can always connect later from your profile.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            id="btn-onboarding-spotify-connect"
            className="w-full"
            style={{ backgroundColor: domainColor.music, color: colors.paper }}
            onClick={handleSpotifyConnect}
          >
            Connect Spotify
          </Button>
          <button
            id="btn-onboarding-spotify-skip"
            className="w-full text-sm hover:opacity-80 transition-opacity py-2"
            style={{ fontFamily: fontFamily.body, color: colors.interchange }}
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
          <h2 className="text-xl font-bold" style={{ fontFamily: fontFamily.display, color: colors.ink }}>Connect AniList</h2>
          <p className="text-sm max-w-xs mx-auto" style={{ fontFamily: fontFamily.body, color: colors.interchange }}>
            We'll import your watch history and ratings to instantly personalise anime
            recommendations. You can always connect later.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            id="btn-onboarding-anilist-connect"
            className="w-full"
            style={{ backgroundColor: domainColor.anime, color: colors.paper }}
            onClick={handleAniListConnect}
          >
            Connect AniList
          </Button>
          <button
            id="btn-onboarding-anilist-skip"
            className="w-full text-sm hover:opacity-80 transition-opacity py-2"
            style={{ fontFamily: fontFamily.body, color: colors.interchange }}
            onClick={handleSkip}
          >
            Skip for now
          </button>
        </div>
      </>
    )
  }

  function StepLocation() {
    return (
      <>
        <div className="text-center space-y-2 mb-8">
          <div
            className="w-12 h-12 flex items-center justify-center rounded-full mx-auto mb-4"
            style={{ background: "rgba(139,135,168,0.12)", border: "1px solid rgba(139,135,168,0.25)" }}
          >
            <span style={{ fontSize: 22, color: colors.interchange }}>⊙</span>
          </div>
          <h2 className="text-xl font-bold" style={{ fontFamily: fontFamily.display, color: colors.ink }}>Allow Location</h2>
          <p className="text-sm max-w-xs mx-auto" style={{ fontFamily: fontFamily.body, color: colors.interchange }}>
            Used only to find restaurants near you — never stored on our servers.
            You can always allow this later.
          </p>
        </div>

        {locationStatus === "requesting" && (
          <p className="text-center text-sm mb-4" style={{ fontFamily: fontFamily.mono, color: colors.interchange }}>
            Requesting your location…
          </p>
        )}
        {locationStatus === "granted" && (
          <p className="text-center text-sm mb-4" style={{ fontFamily: fontFamily.mono, color: domainColor.music }}>
            Location granted ✓
          </p>
        )}
        {locationStatus === "denied" && (
          <p className="text-center text-sm mb-4" style={{ fontFamily: fontFamily.mono, color: domainColor.anime }}>
            Location denied — you can set a city in the restaurants tab.
          </p>
        )}

        {locationStatus === "idle" && (
          <div className="flex flex-col gap-3">
            <Button
              id="btn-onboarding-location-allow"
              className="w-full"
              style={{ backgroundColor: colors.ink, color: colors.paper }}
              onClick={handleLocationRequest}
            >
              Allow Location
            </Button>
            <button
              id="btn-onboarding-location-skip"
              className="w-full text-sm hover:opacity-80 transition-opacity py-2"
              style={{ fontFamily: fontFamily.body, color: colors.interchange }}
              onClick={handleSkip}
            >
              Skip for now
            </button>
          </div>
        )}
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
            <span style={{ fontSize: 22, color: colors.ink }}>✓</span>
          </div>
          <h2 className="text-xl font-bold" style={{ fontFamily: fontFamily.display, color: colors.ink }}>You're all set!</h2>
          <p className="text-sm max-w-xs mx-auto" style={{ fontFamily: fontFamily.body, color: colors.interchange }}>
            Your Taste Passport is ready. Connect any remaining services from your profile
            page whenever you like.
          </p>
        </div>

        <Button
          id="btn-onboarding-finish"
          className="w-full"
          style={{ backgroundColor: colors.ink, color: colors.paper }}
          onClick={finish}
        >
          Go to Dashboard
        </Button>
      </>
    )
  }

  // ── Render ────────────────────────────────────────────────────────

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card
        className="w-full max-w-sm overflow-hidden"
      >
        <div className="p-8">
          {step !== "welcome" && step !== "done" && <ProgressDots />}

          {step === "welcome"  && <StepWelcome />}
          {step === "spotify"  && <StepSpotify />}
          {step === "anilist"  && <StepAniList />}
          {step === "location" && <StepLocation />}
          {step === "done"     && <StepDone />}
        </div>
      </Card>
    </div>
  )
}
