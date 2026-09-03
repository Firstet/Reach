"use client";

import { useState, FormEvent, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useCustomization } from "./components/ThemeApplicator";

export default function RavenLandingPage() {
  const router = useRouter();
  const customization = useCustomization();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [email, setEmail] = useState("admin@rayvensc.com");
  const [password, setPassword] = useState("admin123456");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      setIsLoggedIn(true);
    }
    if (typeof window !== "undefined" && window.location.search.includes("expired=1")) {
      setError("Your session expired. Please sign in again.");
      setShowLoginModal(true);
    }
  }, []);

  const handleLoginClick = () => {
    if (isLoggedIn) {
      router.push("/dashboard");
    } else {
      setShowLoginModal(true);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 401 || res.status === 403) {
          setError(data.detail || "Invalid email or password");
        } else {
          setError(data.detail || `Server returned error (${res.status}). Please check backend.`);
        }
        setLoading(false);
        return;
      }

      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      router.push("/dashboard");
    } catch {
      setError("Unable to connect to server backend. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "relative",
        minHeight: "100vh",
        width: "100vw",
        overflow: "hidden",
        backgroundColor: "#07080a",
        backgroundImage: "radial-gradient(circle at 50% 42%, rgba(212, 175, 55, 0.08) 0%, rgba(7, 8, 10, 0.95) 70%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "#ffffff",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        padding: "24px",
      }}
    >
      {/* Abstract Golden Ambient Light Waves (Reference Image Background) */}
      <svg
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: "55%",
          pointerEvents: "none",
          zIndex: 1,
          opacity: 0.85,
        }}
        viewBox="0 0 1440 600"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="goldWave1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#d4af37" stopOpacity="0.02" />
            <stop offset="35%" stopColor="#f5d77f" stopOpacity="0.35" />
            <stop offset="70%" stopColor="#b8860b" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#d4af37" stopOpacity="0.01" />
          </linearGradient>
          <linearGradient id="goldWave2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#aa7c11" stopOpacity="0.01" />
            <stop offset="50%" stopColor="#ffd700" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#8a6508" stopOpacity="0.02" />
          </linearGradient>
          <filter id="goldGlow" x="-10%" y="-10%" width="120%" height="120%">
            <feGaussianBlur stdDeviation="12" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Ambient Wave Lines */}
        <path
          d="M-100 520 C 300 420, 700 580, 1540 380"
          stroke="url(#goldWave1)"
          strokeWidth="3.5"
          filter="url(#goldGlow)"
        />
        <path
          d="M-100 540 C 400 360, 900 590, 1540 420"
          stroke="url(#goldWave2)"
          strokeWidth="2.5"
          filter="url(#goldGlow)"
        />
        <path
          d="M-100 480 C 250 560, 800 390, 1540 510"
          stroke="url(#goldWave1)"
          strokeWidth="1.5"
          strokeDasharray="6 8"
          opacity="0.6"
        />
        <path
          d="M-100 580 C 500 460, 1000 540, 1540 460"
          stroke="url(#goldWave2)"
          strokeWidth="1.2"
          opacity="0.4"
        />
      </svg>

      {/* Main Content Container - Vertically & Horizontally Centered */}
      <main
        style={{
          position: "relative",
          zIndex: 10,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          maxWidth: "1100px",
          width: "100%",
          animation: "fadeIn 1.2s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {/* Raven Official Emblem Logo */}
        <div style={{ marginBottom: "24px" }}>
          <img
            src={customization?.logo_url || "/logo.svg"}
            alt="Logo Emblem"
            width="88"
            height="88"
            style={{
              filter: "drop-shadow(0 6px 28px rgba(247, 148, 29, 0.45))",
              borderRadius: "20px",
              objectFit: "contain",
            }}
          />
        </div>

        {/* Brand Title / Wordmark */}
        <h1
          style={{
            fontSize: "clamp(38px, 6vw, 64px)",
            fontWeight: "900",
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            margin: 0,
            lineHeight: 1,
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            alignItems: "center",
            gap: "16px",
          }}
        >
          {(() => {
            const titleText = customization?.hero_title || "RAVEN AI";
            const parts = titleText.trim().split(" ");
            if (parts.length > 1) {
              const mainPart = parts.slice(0, -1).join(" ");
              const highlightPart = parts[parts.length - 1];
              return (
                <>
                  <span style={{ color: "#ffffff" }}>{mainPart}</span>
                  <span
                    style={{
                      background: "linear-gradient(135deg, #fbb03b 0%, #f7941d 55%, #d36f0a 100%)",
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                    }}
                  >
                    {highlightPart}
                  </span>
                </>
              );
            }
            return <span style={{ color: "#ffffff" }}>{titleText}</span>;
          })()}
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontSize: "clamp(16px, 2.2vw, 22px)",
            fontWeight: "400",
            color: "#a0a5b5",
            letterSpacing: "0.04em",
            marginTop: "14px",
            marginBottom: "20px",
          }}
        >
          {customization?.hero_subtitle || "AI Business Development Agent"}
        </p>

        {/* Thin Subtle Gold Divider */}
        <div
          style={{
            width: "120px",
            height: "1px",
            background: "linear-gradient(90deg, transparent 0%, rgba(247, 148, 29, 0.65) 50%, transparent 100%)",
            marginBottom: "28px",
          }}
        />

        {/* Single Capability Line matching Reference Image */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexWrap: "wrap",
            gap: "12px 18px",
            fontSize: "clamp(12px, 1.4vw, 15px)",
            fontWeight: "500",
            color: "#e2e6f0",
            letterSpacing: "0.02em",
            marginBottom: "36px",
            padding: "0 16px",
          }}
        >
          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#f7941d", fontSize: "14px" }}>🔍</span> Find leads
          </span>
          <span style={{ color: "rgba(247, 148, 29, 0.35)", fontWeight: "300" }}>|</span>

          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#f7941d", fontSize: "14px" }}>🏢</span> Research companies
          </span>
          <span style={{ color: "rgba(247, 148, 29, 0.35)", fontWeight: "300" }}>|</span>

          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#f7941d", fontSize: "14px" }}>✨</span> Personalize outreach
          </span>
          <span style={{ color: "rgba(247, 148, 29, 0.35)", fontWeight: "300" }}>|</span>

          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#f7941d", fontSize: "14px" }}>💬</span> Engage & follow up
          </span>
          <span style={{ color: "rgba(247, 148, 29, 0.35)", fontWeight: "300" }}>|</span>

          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#f7941d", fontSize: "14px" }}>☑</span> Answer & qualify
          </span>
          <span style={{ color: "rgba(247, 148, 29, 0.35)", fontWeight: "300" }}>|</span>

          <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#f7941d", fontSize: "14px" }}>👤</span> Handoff to you
          </span>
        </div>

        {/* Primary CTA Button - Warm Amber Gold Gradient */}
        <button
          onClick={handleLoginClick}
          style={{
            background: "linear-gradient(135deg, #fbb03b 0%, #f7941d 50%, #d36f0a 100%)",
            color: "#0a0b0e",
            border: "1px solid rgba(251, 176, 59, 0.6)",
            borderRadius: "14px",
            padding: "16px 44px",
            fontSize: "16px",
            fontWeight: "800",
            letterSpacing: "0.03em",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "10px",
            boxShadow: "0 8px 32px rgba(247, 148, 29, 0.4), 0 2px 8px rgba(0, 0, 0, 0.8)",
            transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
            transform: "translateY(0)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-3px)";
            e.currentTarget.style.boxShadow = "0 14px 44px rgba(247, 148, 29, 0.6), 0 4px 12px rgba(0, 0, 0, 0.9)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "0 8px 32px rgba(247, 148, 29, 0.4), 0 2px 8px rgba(0, 0, 0, 0.8)";
          }}
        >
          <span style={{ fontSize: "16px" }}>🔒</span>
          <span>{isLoggedIn ? "Enter Raven AI Dashboard" : "Login to Raven AI"}</span>
        </button>

        {/* Trust Footnote */}
        <p
          style={{
            fontSize: "12px",
            color: "rgba(255, 255, 255, 0.45)",
            marginTop: "24px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            letterSpacing: "0.03em",
          }}
        >
          <span>🛡</span> Secure. Intelligent. Built for Growth.
        </p>
      </main>

      {/* Authentication Login Modal */}
      {showLoginModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(3, 4, 6, 0.85)",
            backdropFilter: "blur(12px)",
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            animation: "fadeIn 0.3s ease",
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowLoginModal(false);
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "400px",
              background: "#0d0e14",
              border: "1px solid rgba(212, 175, 55, 0.3)",
              borderRadius: "20px",
              padding: "36px 30px",
              boxShadow: "0 24px 80px rgba(0,0,0,0.9), 0 0 40px rgba(212,175,55,0.15)",
              position: "relative",
            }}
          >
            {/* Modal Header */}
            <div style={{ textAlign: "center", marginBottom: "28px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "800", color: "#ffffff", marginBottom: "6px" }}>
                Login to <span style={{ color: "#d4af37" }}>RAVEN AI</span>
              </h2>
              <p style={{ fontSize: "12px", color: "#8a90a2" }}>
                Enter your administrative credentials to access the workspace
              </p>
            </div>

            {error && (
              <div
                style={{
                  background: "rgba(255, 77, 77, 0.12)",
                  border: "1px solid rgba(255, 77, 77, 0.3)",
                  color: "#ff6b6b",
                  borderRadius: "10px",
                  padding: "10px 14px",
                  fontSize: "12px",
                  marginBottom: "20px",
                  textAlign: "center",
                }}
              >
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: "18px" }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: "700",
                    color: "rgba(255, 255, 255, 0.6)",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    marginBottom: "8px",
                  }}
                >
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="admin@rayvensc.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(255, 255, 255, 0.04)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "10px",
                    padding: "12px 14px",
                    color: "#ffffff",
                    fontSize: "14px",
                    outline: "none",
                    transition: "border 0.2s",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#d4af37")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.12)")}
                />
              </div>

              <div style={{ marginBottom: "26px" }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: "700",
                    color: "rgba(255, 255, 255, 0.6)",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    marginBottom: "8px",
                  }}
                >
                  Password
                </label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(255, 255, 255, 0.04)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "10px",
                    padding: "12px 14px",
                    color: "#ffffff",
                    fontSize: "14px",
                    outline: "none",
                    transition: "border 0.2s",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#d4af37")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.12)")}
                />
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setShowLoginModal(false)}
                  style={{
                    flex: 1,
                    background: "transparent",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    color: "#a0a5b5",
                    borderRadius: "10px",
                    padding: "12px",
                    fontSize: "13px",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    flex: 2,
                    background: "linear-gradient(135deg, #f5d77f 0%, #d4af37 100%)",
                    color: "#0a0b0e",
                    border: "none",
                    borderRadius: "10px",
                    padding: "12px",
                    fontSize: "13px",
                    fontWeight: "800",
                    cursor: "pointer",
                  }}
                >
                  {loading ? "Authenticating..." : "Sign In"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Global CSS for fade-in animations */}
      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
