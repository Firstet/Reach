"use client";

import { useEffect, useState } from "react";

const PROVIDER_TYPES = [
  { type: "appearance", label: "Home Page & Theme", providers: ["home_customization"], icon: "🎨" },
  { type: "llm", label: "AI Engine & Personalization", providers: ["openai", "openai_compatible", "anthropic", "gemini", "ollama"], icon: "🧠" },
  { type: "email", label: "Email Sending (SMTP / OAuth)", providers: ["smtp", "gmail", "outlook"], icon: "📧" },
  { type: "branding", label: "Branding & Rayven Pitches", providers: ["rayvensc_branding"], icon: "🏛️" },
  { type: "search", label: "Web Search & Discovery", providers: ["serper", "serpapi", "brave"], icon: "🔍" },
  { type: "enrichment", label: "EMAIL & LEAD DATA", providers: ["none", "hunter", "apollo", "clearbit"], icon: "⚗" },
  { type: "linkedin", label: "LinkedIn Automation", providers: ["playwright"], icon: "🔗" },
  { type: "notification", label: "Escalation & Alerts", providers: ["slack", "webhook"], icon: "🔔" },
];

const PROVIDER_FIELDS: Record<string, Array<{ key: string; label: string; secret?: boolean; hint?: string; textarea?: boolean; select?: boolean; options?: string[] }>> = {
  home_customization: [
    {
      key: "font_family",
      label: "Platform Font Family",
      select: true,
      options: ["Inter", "Outfit", "Plus Jakarta Sans", "Roboto", "Space Grotesk", "Playfair Display", "System Default"],
      hint: "Select primary typography style for the home page and platform UI",
    },
    {
      key: "font_size_scale",
      label: "Base Font Size Scale",
      select: true,
      options: ["14px", "15px", "16px", "18px", "20px"],
      hint: "Base font scale across the platform",
    },
    { key: "logo_url", label: "Home & Platform Logo URL", hint: "/logo.svg or https://yourdomain.com/logo.png" },
    { key: "favicon_url", label: "Browser Favicon URL", hint: "/favicon.svg or https://yourdomain.com/favicon.ico" },
    { key: "hero_title", label: "Home Page Title / Heading", hint: "RAVEN AI" },
    { key: "hero_subtitle", label: "Home Page Subtitle / Tagline", hint: "AI Business Development Agent" },
  ],
  openai: [
    { key: "api_key", label: "OpenAI API Key", secret: true },
    { key: "model", label: "Default Model", hint: "gpt-4o" },
    { key: "embedding_model", label: "Embedding Model", hint: "text-embedding-3-small" },
    {
      key: "system_prompt_personalization",
      label: "AI Personalization & Rayven Pitch Strategy Prompt",
      textarea: true,
      hint: "Analyze prospect company context (website, social handles, leadership). Evaluate missing capabilities: 1) Web design/revamp needed? 2) Corporate PR & Strategic Narrative needed? 3) Executive/Founder personal branding on LinkedIn needed? 4) Digital growth/reputation needed? Frame consultative cold outreach aligned with RayvenSC methodology.",
    },
  ],
  openai_compatible: [
    { key: "base_url", label: "Custom Provider Base URL", hint: "https://api.groq.com/openai/v1 or https://api.deepseek.com/v1" },
    { key: "api_key", label: "API Key", secret: true, hint: "gsk_... / sk-..." },
    { key: "model", label: "Model ID", hint: "llama-3.3-70b-versatile / deepseek-chat / qwen-2.5-72b" },
    { key: "embedding_model", label: "Embedding Model ID", hint: "text-embedding-3-small" },
    {
      key: "system_prompt_personalization",
      label: "AI Personalization & Rayven Pitch Strategy Prompt",
      textarea: true,
      hint: "Personalization guidelines for Rayven Strategic Communications outreach.",
    },
  ],
  anthropic: [
    { key: "api_key", label: "Anthropic API Key", secret: true },
    { key: "model", label: "Model", hint: "claude-3-5-sonnet-20241022" },
    {
      key: "system_prompt_personalization",
      label: "AI Personalization & Rayven Pitch Strategy Prompt",
      textarea: true,
      hint: "Evaluate company digital presence and customize outreach.",
    },
  ],
  gemini: [
    { key: "api_key", label: "Google Gemini API Key", secret: true },
    { key: "model", label: "Model", hint: "gemini-1.5-pro" },
  ],
  ollama: [
    { key: "base_url", label: "Ollama Base URL", hint: "http://localhost:11434" },
    { key: "model", label: "Local Model", hint: "llama3.1" },
  ],
  smtp: [
    { key: "smtp_host", label: "SMTP Server Host", hint: "smtp.gmail.com or smtp.mailgun.org" },
    { key: "smtp_port", label: "SMTP Server Port", hint: "587 (TLS) or 465 (SSL)" },
    { key: "smtp_username", label: "SMTP Username / Email", secret: false, hint: "outreach@rayvensc.com" },
    { key: "smtp_password", label: "SMTP Password / App Password", secret: true },
    { key: "sender_name", label: "Sender Display Name", hint: "Rayven Strategic Communications" },
    { key: "sender_email", label: "From / Reply-To Email", hint: "contact@rayvensc.com" },
    { key: "use_tls", label: "Enable STARTTLS", hint: "true" },
  ],
  gmail: [
    { key: "client_id", label: "OAuth Client ID", secret: true },
    { key: "client_secret", label: "OAuth Client Secret", secret: true },
    { key: "refresh_token", label: "Refresh Token", secret: true },
    { key: "sender_email", label: "Sender Email", hint: "outreach@rayvensc.com" },
  ],
  outlook: [
    { key: "client_id", label: "Azure App Client ID", secret: true },
    { key: "client_secret", label: "Azure Client Secret", secret: true },
    { key: "tenant_id", label: "Azure Tenant ID", hint: "common" },
    { key: "sender_email", label: "Sender Email" },
  ],
  rayvensc_branding: [
    { key: "company_name", label: "Company Name", hint: "Rayven Strategic Communications" },
    { key: "tagline", label: "Tagline", hint: "Context Intelligence · Narrative Architecture · Strategic Deployment" },
    { key: "logo_url", label: "Company Logo Image URL", hint: "https://rayvensc.com/logo.png" },
    { key: "sender_persona", label: "Default Sender Persona", hint: "Executive / Founder Voice" },
    { key: "website_pitch_angle", label: "Web Creation / Revamp Pitch Angle", textarea: true, hint: "Pitched when lead company has no website or an outdated site." },
    { key: "pr_pitch_angle", label: "Corporate PR & Strategic Narrative Pitch Angle", textarea: true, hint: "Pitched when lead needs press visibility and brand authority." },
    { key: "founder_pitch_angle", label: "Executive / Founder Personal Branding Pitch Angle", textarea: true, hint: "Pitched directly to CEOs and Founders for LinkedIn leadership." },
    { key: "email_footer_html", label: "HTML Email Footer / Signature", textarea: true, hint: "<p>Warm regards,<br/><strong>Rayven Strategic Communications</strong><br/>Abuja, Nigeria · https://rayvensc.com</p>" },
  ],
  none: [],
  hunter: [
    { key: "api_key", label: "Hunter.io API Key", secret: true },
  ],
  apollo: [
    { key: "api_key", label: "Apollo API Key", secret: true },
  ],
  clearbit: [
    { key: "api_key", label: "Clearbit API Key", secret: true },
  ],
  serper: [
    { key: "api_key", label: "Serper Google Search API Key", secret: true },
  ],
  serpapi: [
    { key: "api_key", label: "SerpAPI Key", secret: true },
  ],
  brave: [
    { key: "api_key", label: "Brave Search API Key", secret: true },
  ],
  slack: [
    { key: "webhook_url", label: "Slack Webhook URL", secret: true },
    { key: "channel", label: "Notification Channel", hint: "#bd-alerts" },
  ],
  webhook: [
    { key: "url", label: "Webhook Endpoint URL" },
    { key: "secret", label: "Webhook Signing Secret", secret: true },
  ],
  playwright: [
    { key: "session_cookie", label: "LinkedIn li_at Cookie", secret: true, hint: "Cookie value from authenticated browser" },
    { key: "rate_limit_per_hour", label: "Rate Limit (per hour)", hint: "20" },
  ],
};

async function apiFetch(path: string, opts?: RequestInit) {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const url = path;

  const res = await fetch(url, {
    ...opts,
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
      "Content-Type": "application/json",
      ...opts?.headers,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Request failed");
    throw new Error(errorText);
  }
  return res.json();
}

export default function ConfigPage() {
  const [health, setHealth] = useState<Record<string, any>>({});
  const [activeSection, setActiveSection] = useState("appearance");
  const [activeProvider, setActiveProvider] = useState("home_customization");
  const [emailPolicy, setEmailPolicy] = useState("verified_only");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [savedConfigs, setSavedConfigs] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const loadConfigs = async () => {
    try {
      const data = await apiFetch("/api/v1/config");
      const map: Record<string, any> = {};
      (data.providers || []).forEach((item: any) => {
        map[item.provider_name] = item;
      });
      setSavedConfigs(map);
    } catch {
      /* ignore */
    }
  };

  const loadHealth = async () => {
    try {
      const data = await apiFetch("/api/v1/config/health");
      setHealth(data.providers || {});
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    loadHealth();
    loadConfigs();
  }, []);

  // When activeProvider changes, prefill form with existing saved settings or default RayvenSC copy
  useEffect(() => {
    const existing = savedConfigs[activeProvider];
    if (existing) {
      const initial: Record<string, string> = { ...(existing.config_data || {}) };
      if (existing.secrets) {
        Object.entries(existing.secrets).forEach(([k, v]) => {
          initial[k] = v ? "***" : "";
        });
      }
      setFieldValues(initial);
    } else if (activeProvider === "home_customization") {
      setFieldValues({
        font_family: "Inter",
        font_size_scale: "16px",
        logo_url: "/logo.svg",
        favicon_url: "/favicon.svg",
        hero_title: "RAVEN AI",
        hero_subtitle: "AI Business Development Agent",
      });
    } else if (activeProvider === "rayvensc_branding") {
      setFieldValues({
        company_name: "Rayven Strategic Communications",
        tagline: "Context Intelligence · Narrative Architecture · Strategic Deployment",
        logo_url: "https://rayvensc.com/logo.png",
        sender_persona: "Executive & Founder Advisory Voice",
        website_pitch_angle: "We craft modern, high-trust digital platforms and web applications for enterprise leaders that establish instant authority and digital growth.",
        pr_pitch_angle: "We architect corporate narratives, securing tier-1 media positioning, PR coverage, and executive reputation management across target markets.",
        founder_pitch_angle: "We build personal brand positioning for CEOs, Founders, and C-Suite leaders to transform executive presence into high-trust inbound partnerships.",
        email_footer_html: "<p>Warm regards,<br/><strong>Rayven Strategic Communications</strong><br/>Abuja, Nigeria · <a href='https://rayvensc.com'>rayvensc.com</a></p>",
      });
    } else {
      setFieldValues({});
    }
  }, [activeProvider, savedConfigs]);


  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    const fields = PROVIDER_FIELDS[activeProvider] || [];
    const secrets: Record<string, string> = {};
    const config: Record<string, string> = { email_policy: emailPolicy };

    fields.forEach(({ key, secret }) => {
      const val = fieldValues[key] || "";
      if (secret) {
        if (val && val !== "***") {
          secrets[key] = val;
        }
      } else {
        config[key] = val;
      }
    });

    try {
      await apiFetch("/api/v1/config", {
        method: "PUT",
        body: JSON.stringify({
          provider_type: activeSection,
          provider_name: activeProvider,
          is_active: true,
          config_data: config,
          secrets,
        }),
      });
      setSaved(true);
      await loadHealth();
      await loadConfigs();
      setTimeout(() => setSaved(false), 2500);
    } catch (e: any) {
      alert("Failed to save provider settings: " + (e?.message || e));
    } finally {
      setSaving(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: "var(--bg-secondary, #1a1a26)",
    border: "1px solid var(--border, #2a2a3c)",
    borderRadius: "8px",
    padding: "10px 12px",
    color: "var(--text-primary, #ffffff)",
    fontSize: "13px",
    outline: "none",
  };

  const currentSection = PROVIDER_TYPES.find((s) => s.type === activeSection);
  const fields = PROVIDER_FIELDS[activeProvider] || [];

  return (
    <div style={{ padding: "32px", maxWidth: "1200px" }}>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "22px", fontWeight: "900", letterSpacing: "-0.02em", marginBottom: "6px" }}>
          Settings & Provider Engine Configuration
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary, #9494a8)", lineHeight: "1.5" }}>
          Configure AI Personalization engines, SMTP email credentials, optional Email & Lead Data providers, and RayvenSC branding.
        </p>
      </div>

      {/* Health status bar */}
      <div
        style={{
          background: "var(--bg-card, #12121c)",
          border: "1px solid var(--border, #2a2a3c)",
          borderRadius: "12px",
          padding: "16px 20px",
          marginBottom: "24px",
          display: "flex",
          gap: "16px",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: "11px", fontWeight: "700", color: "#71718a", letterSpacing: "0.06em", textTransform: "uppercase" }}>
          Active Engine Health
        </span>
        {Object.entries(health).map(([key, val]: any) => (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <div
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: val.healthy ? "#4cb89c" : "#c94c4c",
              }}
            />
            <span style={{ fontSize: "12px", color: "var(--text-secondary)", textTransform: "capitalize" }}>
              {key}: <strong>{val.name || "—"}</strong>
            </span>
          </div>
        ))}
        {Object.keys(health).length === 0 && (
          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            Backend operational — configure settings below to activate services
          </span>
        )}
        <button
          onClick={loadHealth}
          style={{
            marginLeft: "auto",
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            padding: "6px 14px",
            color: "var(--text-secondary)",
            fontSize: "12px",
            fontWeight: "600",
            cursor: "pointer",
          }}
        >
          ↻ Refresh Status
        </button>
      </div>

      <div style={{ display: "flex", gap: "20px" }}>
        {/* Sidebar Sections */}
        <div
          style={{
            width: "240px",
            flexShrink: 0,
            background: "var(--bg-card, #12121c)",
            border: "1px solid var(--border, #2a2a3c)",
            borderRadius: "14px",
            padding: "10px",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          {PROVIDER_TYPES.map((section) => (
            <button
              key={section.type}
              onClick={() => {
                setActiveSection(section.type);
                setActiveProvider(section.providers[0]);
                setFieldValues({});
              }}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "12px 14px",
                borderRadius: "10px",
                border: "none",
                background: activeSection === section.type ? "rgba(201,168,76,0.15)" : "transparent",
                color: activeSection === section.type ? "#c9a84c" : "var(--text-secondary, #9494a8)",
                fontSize: "13px",
                fontWeight: activeSection === section.type ? "700" : "500",
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.15s ease",
              }}
            >
              <span style={{ fontSize: "16px" }}>{section.icon}</span>
              <span>{section.label}</span>
            </button>
          ))}
        </div>

        {/* Configuration Body Panel */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              background: "var(--bg-card, #12121c)",
              border: "1px solid var(--border, #2a2a3c)",
              borderRadius: "14px",
              overflow: "hidden",
            }}
          >
            {/* Header / Tabs */}
            <div
              style={{
                display: "flex",
                borderBottom: "1px solid var(--border, #2a2a3c)",
                background: "rgba(0,0,0,0.2)",
              }}
            >
              {currentSection?.providers.map((p) => (
                <button
                  key={p}
                  onClick={() => {
                    setActiveProvider(p);
                    setFieldValues({});
                  }}
                  style={{
                    padding: "14px 24px",
                    background: activeProvider === p ? "var(--bg-card)" : "transparent",
                    border: "none",
                    borderBottom: activeProvider === p ? "3px solid #c9a84c" : "3px solid transparent",
                    color: activeProvider === p ? "#c9a84c" : "var(--text-muted, #71718a)",
                    fontSize: "13px",
                    fontWeight: "700",
                    cursor: "pointer",
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                  }}
                >
                  {p === "none" ? "None (Zero-Paid API Mode)" : p.replace(/_/g, " ")}
                </button>
              ))}
            </div>

            {/* Config Form */}
            <form onSubmit={handleSave} style={{ padding: "28px" }}>
              {activeSection === "enrichment" ? (
                <div>
                  <h2 style={{ fontSize: "16px", fontWeight: "800", color: "#ffffff", marginBottom: "4px" }}>
                    EMAIL & LEAD DATA
                  </h2>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "20px" }}>
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>Status:</span>
                    <span style={{ fontSize: "12px", fontWeight: "700", color: "#4cb89c", background: "rgba(76,184,156,0.15)", padding: "2px 8px", borderRadius: "4px" }}>
                      Optional
                    </span>
                  </div>

                  <div style={{ marginBottom: "20px" }}>
                    <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "#71718a", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px" }}>
                      Provider
                    </label>
                    <select
                      id="enrichment-provider-select"
                      value={activeProvider}
                      onChange={(e) => {
                        setActiveProvider(e.target.value);
                        setFieldValues({});
                      }}
                      style={inputStyle}
                    >
                      <option value="none">None (Zero-Paid API Mode)</option>
                      <option value="hunter">Hunter.io</option>
                      <option value="apollo">Apollo.io</option>
                      <option value="clearbit">Clearbit</option>
                    </select>
                  </div>

                  <div style={{ marginBottom: "20px" }}>
                    <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "#71718a", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px" }}>
                      Email policy
                    </label>
                    <select
                      id="email-policy-select"
                      value={emailPolicy}
                      onChange={(e) => setEmailPolicy(e.target.value)}
                      style={inputStyle}
                    >
                      <option value="verified_only">Verified only</option>
                      <option value="high_confidence">High Confidence Only (Score &gt;= 70)</option>
                      <option value="any_email">Any Email</option>
                    </select>
                  </div>

                  {activeProvider === "none" && (
                    <div
                      style={{
                        background: "rgba(76,184,156,0.06)",
                        border: "1px solid rgba(76,184,156,0.2)",
                        borderRadius: "10px",
                        padding: "16px",
                        marginBottom: "20px",
                        fontSize: "12px",
                        color: "var(--text-secondary)",
                        lineHeight: "1.6",
                      }}
                    >
                      💡 <strong>No Paid Provider Mode Active:</strong> The system discovers leads using public search, company website research, public contact extraction, and authenticated LinkedIn browser sessions. Unverified emails will never be marked as verified or fabricated.
                    </div>
                  )}
                </div>
              ) : (
                <div
                  style={{
                    background: "rgba(201,168,76,0.06)",
                    border: "1px solid rgba(201,168,76,0.2)",
                    borderRadius: "10px",
                    padding: "14px 18px",
                    marginBottom: "24px",
                    fontSize: "12px",
                    color: "#d4af37",
                    lineHeight: "1.6",
                  }}
                >
                  🔒 <strong>Secure Configuration:</strong> Sensitive credentials (API keys, SMTP passwords, tokens) are encrypted before database storage. Existing credentials show as <code>***</code>. Leave blank to keep existing values.
                </div>
              )}

              {fields.length > 0 &&
                fields.map(({ key, label, secret, hint, textarea, select, options }) => (
                  <div key={key} style={{ marginBottom: "20px" }}>
                    <label
                      style={{
                        display: "block",
                        fontSize: "11px",
                        fontWeight: "700",
                        color: "var(--text-muted, #71718a)",
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                        marginBottom: "8px",
                      }}
                    >
                      {label}
                    </label>
                    {select ? (
                      <select
                        value={fieldValues[key] || options?.[0] || ""}
                        onChange={(e) => setFieldValues((f) => ({ ...f, [key]: e.target.value }))}
                        style={inputStyle}
                      >
                        {options?.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : textarea ? (
                      <textarea
                        rows={4}
                        placeholder={hint || ""}
                        value={fieldValues[key] || ""}
                        onChange={(e) => setFieldValues((f) => ({ ...f, [key]: e.target.value }))}
                        style={{
                          ...inputStyle,
                          resize: "vertical",
                          fontFamily: "inherit",
                          lineHeight: "1.5",
                        }}
                      />
                    ) : (
                      <input
                        type={secret ? "password" : "text"}
                        placeholder={secret ? "••••••••" : hint || ""}
                        value={fieldValues[key] || ""}
                        onChange={(e) => setFieldValues((f) => ({ ...f, [key]: e.target.value }))}
                        style={inputStyle}
                      />
                    )}
                  </div>
                ))}

              <div style={{ display: "flex", gap: "12px", marginTop: "28px" }}>
                <button
                  id="save-provider-config"
                  type="submit"
                  disabled={saving}
                  style={{
                    background: saved
                      ? "rgba(76,184,156,0.2)"
                      : "linear-gradient(135deg, #c9a84c, #a87830)",
                    border: saved ? "1px solid rgba(76,184,156,0.5)" : "none",
                    borderRadius: "10px",
                    padding: "12px 28px",
                    color: saved ? "#4cb89c" : "#0a0a0f",
                    fontSize: "14px",
                    fontWeight: "800",
                    cursor: saving ? "not-allowed" : "pointer",
                    transition: "all 0.2s ease",
                    boxShadow: saved ? "none" : "0 4px 16px rgba(201,168,76,0.2)",
                  }}
                >
                  {saving ? "Saving Changes..." : saved ? "✓ Settings Saved" : "Save Settings"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
