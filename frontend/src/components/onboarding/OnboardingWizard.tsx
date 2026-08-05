import { useState } from "react"
import { api } from "../../api"
import { Button } from "../ui"

// ── Style constants reused from App.tsx ──────────────────────────────
const GLASS_PANEL = {
  background:     "rgba(18,24,31,0.75)",
  backdropFilter: "blur(10px)",
  border:         "1px solid rgba(255,255,255,0.06)",
  borderRadius:   "0.75rem",
} as const

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

  function ProgressDots() {
    return (
      <div className="flex items-center justify-center gap-1.5 mb-8">
        {STEPS.slice(0, -1).map((_, i) => (
          <div
            key={i}
            style={{
              width:        i === stepIndex ? 20 : 6,
              height:       6,
              borderRadius: 3,
              background:   i <= stepIndex ? "rgba(124,108,240,0.9)" : "rgba(255,255,255,0.12)",
              transition:   "all 0.3s ease",
            }}
          />
        ))}
      </div>
    )
  }

  // ── Step renders ─────────────────────────────────────────────────

  function StepWelcome() {
    return (
      <>
        <div className="text-center space-y-3 mb-8">
          <h1 className="text-2xl font-display font-bold text-foreground">
            Welcome to Poly Taste
          </h1>
          <p className="text-sm font-sans text-muted-foreground max-w-sm mx-auto">
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
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}
            >
              <span className="text-lg mt-0.5 text-muted-foreground">{icon}</span>
              <div>
                <p className="text-sm font-sans font-semibold text-foreground">{label}</p>
                <p className="text-xs font-sans text-muted-foreground">{desc}</p>
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
            style={{ background: "rgba(124,108,240,0.12)", border: "1px solid rgba(124,108,240,0.25)" }}
          >
            <span style={{ fontSize: 22, color: "#7C6CF0" }}>♪</span>
          </div>
          <h2 className="text-xl font-display font-bold text-foreground">Connect Spotify</h2>
          <p className="text-sm font-sans text-muted-foreground max-w-xs mx-auto">
            We'll read your top tracks and artists to enrich recommendations across all domains.
            You can always connect later from your profile.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            id="btn-onboarding-spotify-connect"
            className="w-full"
            style={{ backgroundColor: "#7C6CF0", color: "#fff" }}
            onClick={handleSpotifyConnect}
          >
            Connect Spotify
          </Button>
          <button
            id="btn-onboarding-spotify-skip"
            className="w-full text-sm font-sans text-muted-foreground hover:text-foreground transition-colors py-2"
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
            style={{ background: "rgba(74,144,226,0.12)", border: "1px solid rgba(74,144,226,0.25)" }}
          >
            <span style={{ fontSize: 22, color: "#4A90E2" }}>⬡</span>
          </div>
          <h2 className="text-xl font-display font-bold text-foreground">Connect AniList</h2>
          <p className="text-sm font-sans text-muted-foreground max-w-xs mx-auto">
            We'll import your watch history and ratings to instantly personalise anime
            recommendations. You can always connect later.
          </p>
        </div>

        <div className="flex flex-col gap-3">
          <Button
            id="btn-onboarding-anilist-connect"
            className="w-full"
            style={{ backgroundColor: "#4A90E2", color: "#fff" }}
            onClick={handleAniListConnect}
          >
            Connect AniList
          </Button>
          <button
            id="btn-onboarding-anilist-skip"
            className="w-full text-sm font-sans text-muted-foreground hover:text-foreground transition-colors py-2"
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
            style={{ background: "rgba(227,168,87,0.12)", border: "1px solid rgba(227,168,87,0.25)" }}
          >
            <span style={{ fontSize: 22, color: "#E3A857" }}>⊙</span>
          </div>
          <h2 className="text-xl font-display font-bold text-foreground">Allow Location</h2>
          <p className="text-sm font-sans text-muted-foreground max-w-xs mx-auto">
            Used only to find restaurants near you — never stored on our servers.
            You can always allow this later.
          </p>
        </div>

        {locationStatus === "requesting" && (
          <p className="text-center text-sm font-mono text-muted-foreground mb-4">
            Requesting your location…
          </p>
        )}
        {locationStatus === "granted" && (
          <p className="text-center text-sm font-mono mb-4" style={{ color: "#3ED6C4" }}>
            Location granted ✓
          </p>
        )}
        {locationStatus === "denied" && (
          <p className="text-center text-sm font-mono mb-4" style={{ color: "#FF7A59" }}>
            Location denied — you can set a city in the restaurants tab.
          </p>
        )}

        {locationStatus === "idle" && (
          <div className="flex flex-col gap-3">
            <Button
              id="btn-onboarding-location-allow"
              className="w-full"
              style={{ backgroundColor: "#E3A857", color: "#0A0E14" }}
              onClick={handleLocationRequest}
            >
              Allow Location
            </Button>
            <button
              id="btn-onboarding-location-skip"
              className="w-full text-sm font-sans text-muted-foreground hover:text-foreground transition-colors py-2"
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
              background:  "linear-gradient(135deg, rgba(124,108,240,0.2), rgba(62,214,196,0.2))",
              border:      "1px solid rgba(124,108,240,0.3)",
            }}
          >
            <span style={{ fontSize: 22 }}>✓</span>
          </div>
          <h2 className="text-xl font-display font-bold text-foreground">You're all set!</h2>
          <p className="text-sm font-sans text-muted-foreground max-w-xs mx-auto">
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
    <div className="flex min-h-screen items-center justify-center p-4">
      <div
        className="w-full max-w-sm"
        style={GLASS_PANEL}
      >
        <div className="p-8">
          {step !== "welcome" && step !== "done" && <ProgressDots />}

          {step === "welcome"  && <StepWelcome />}
          {step === "spotify"  && <StepSpotify />}
          {step === "anilist"  && <StepAniList />}
          {step === "location" && <StepLocation />}
          {step === "done"     && <StepDone />}
        </div>
      </div>
    </div>
  )
}
