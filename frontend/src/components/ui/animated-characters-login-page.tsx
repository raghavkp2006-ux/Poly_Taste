"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { api } from "@/api";

function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGoogleLogin = () => {
    setError("");
    setIsLoading(true);
    window.location.href = api.auth.googleLoginUrl;
  };

  const handleSkip = () => {
    api.auth
      .login({ email: "guest@poly.taste", password: "guest_password" })
      .catch(() => {})
      .finally(() => window.location.reload());
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ backgroundColor: "#10262A" }}
    >
      {/* Background texture */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: `radial-gradient(circle at 20% 50%, #EFE6D8 0%, transparent 50%),
                            radial-gradient(circle at 80% 20%, #C6318C 0%, transparent 50%)`,
        }}
      />

      <div className="relative z-10 w-full max-w-sm mx-auto text-center space-y-8">
        {/* Logo / Brand */}
        <div className="space-y-3">
          <div
            className="mx-auto w-12 h-12 flex items-center justify-center"
            style={{ backgroundColor: "#EFE6D8" }}
          >
            <span className="text-xl font-display tracking-wide" style={{ color: "#10262A" }}>
              P
            </span>
          </div>
          <h1
            className="text-3xl font-display tracking-wide"
            style={{ color: "#EFE6D8" }}
          >
            Poly_Taste
          </h1>
          <p className="text-sm font-body" style={{ color: "#EFE6D8" + "99" }}>
            Your personal taste passport, stamped.
          </p>
        </div>

        {/* Google Sign-In Button — Sole Primary CTA */}
        <div className="space-y-4">
          <button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className={cn(
              "w-full flex items-center justify-center gap-3 h-12 px-6",
              "border transition-opacity duration-200",
              "hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed",
            )}
            style={{
              backgroundColor: "#EFE6D8",
              borderColor: "#EFE6D8" + "40",
              color: "#10262A",
            }}
          >
            {/* Google 'G' icon */}
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.19 3.32v2.77h3.55c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-1 7.28-2.69l-3.55-2.77c-.99.66-2.25 1.06-3.73 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.72 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.72 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            <span
              className="text-sm font-body font-semibold"
              style={{ color: "#10262A" }}
            >
              {isLoading ? "Signing in…" : "Continue with Google"}
            </span>
          </button>

          {/* Secondary actions */}
          <div className="pt-4 space-y-3">
            <button
              onClick={handleSkip}
              className="w-full flex items-center justify-center h-10 text-sm font-body transition-colors duration-200"
              style={{ color: "#EFE6D8" + "80" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#EFE6D8")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#EFE6D8" + "80")}
            >
              Skip for now — browse anime
            </button>
          </div>
        </div>

        {error && (
          <p className="text-xs font-mono" style={{ color: "#B23A2E" }}>
            {error}
          </p>
        )}

        {/* Footer */}
        <div
          className="pt-8 text-[10px] font-mono uppercase tracking-widest"
          style={{ color: "#EFE6D8" + "40" }}
        >
          <span>Poly_Taste · Taste Passport v1</span>
        </div>
      </div>
    </div>
  );
}

export const Component = LoginPage;
