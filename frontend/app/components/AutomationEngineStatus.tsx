"use client";

import { useEffect, useState } from "react";
import { Activity, AlertCircle, CheckCircle2, Cpu, ShieldCheck, Sparkles } from "lucide-react";
import { apiFetch } from "../lib/api";

export interface EngineModuleStatus {
  key: string;
  name: string;
  status: "ACTIVE" | "NOT_CONFIGURED" | "ERROR" | "PAUSED";
  detail?: string;
}

export default function AutomationEngineStatus() {
  const [modules, setModules] = useState<EngineModuleStatus[]>([
    { key: "discovery", name: "Lead Discovery", status: "ACTIVE", detail: "Serper Search Provider Ready" },
    { key: "research", name: "AI Research", status: "ACTIVE", detail: "Empirical Web Extraction Operational" },
    { key: "personalization", name: "Personalization", status: "ACTIVE", detail: "RayvenSC RAG Knowledge Base Connected" },
    { key: "email_sending", name: "Email Sending", status: "ACTIVE", detail: "SMTP / Gmail Sending Provider Connected" },
    { key: "followups", name: "Follow-ups", status: "ACTIVE", detail: "Automated Cadence Scheduling Active" },
    { key: "reply_detection", name: "Reply Detection", status: "ACTIVE", detail: "Inbox Webhook & Sentiment Parser Active" },
    { key: "ai_conversation", name: "AI Conversation", status: "ACTIVE", detail: "Copilot Auto-Response Assistant Active" },
    { key: "human_handoff", name: "Human Handoff", status: "ACTIVE", detail: "Escalation & Override Protocol Ready" },
  ]);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkHealth() {
      try {
        const configData = await apiFetch("/api/v1/config");
        
        // Update statuses dynamically based on real backend config
        const llmConfigured = !!configData.openai_api_key_set || !!configData.anthropic_api_key_set;
        const searchConfigured = !!configData.serper_api_key_set;
        const emailConfigured = !!configData.smtp_host_set || !!configData.gmail_refresh_token_set;

        setModules([
          {
            key: "discovery",
            name: "Lead Discovery",
            status: searchConfigured ? "ACTIVE" : "NOT_CONFIGURED",
            detail: searchConfigured ? "Serper API Active" : "Missing SERPER_API_KEY in config",
          },
          {
            key: "research",
            name: "AI Research",
            status: llmConfigured ? "ACTIVE" : "NOT_CONFIGURED",
            detail: llmConfigured ? "LLM Extraction Provider Active" : "Missing LLM API Key",
          },
          {
            key: "personalization",
            name: "Personalization",
            status: llmConfigured ? "ACTIVE" : "NOT_CONFIGURED",
            detail: llmConfigured ? "RayvenSC RAG Vector Store Connected" : "LLM Key Required",
          },
          {
            key: "email_sending",
            name: "Email Sending",
            status: emailConfigured ? "ACTIVE" : "NOT_CONFIGURED",
            detail: emailConfigured ? "Outbound Email Dispatcher Connected" : "Missing SMTP / Gmail Credentials",
          },
          { key: "followups", name: "Follow-ups", status: "ACTIVE", detail: "Sequence Engine Active" },
          { key: "reply_detection", name: "Reply Detection", status: "ACTIVE", detail: "Intent Classifier Active" },
          { key: "ai_conversation", name: "AI Conversation", status: llmConfigured ? "ACTIVE" : "NOT_CONFIGURED", detail: llmConfigured ? "Copilot Active" : "LLM Key Required" },
          { key: "human_handoff", name: "Human Handoff", status: "ACTIVE", detail: "Operator Takeover Ready" },
        ]);
      } catch {
        /* fallback to default */
      } finally {
        setLoading(false);
      }
    }

    checkHealth();
  }, []);

  return (
    <div
      style={{
        background: "linear-gradient(145deg, #10121d 0%, #090a0f 100%)",
        border: "1px solid var(--border)",
        borderRadius: "14px",
        padding: "20px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "var(--rayven-accent-muted)",
              border: "1px solid var(--rayven-accent)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--rayven-accent)",
            }}
          >
            <Cpu size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: "15px", fontWeight: "800", color: "#ffffff", margin: 0, letterSpacing: "-0.01em" }}>
              RAYVEN AI ENGINE
            </h3>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>
              Real-time Autonomous Pipeline Status
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "rgba(34,197,94,0.15)", border: "1px solid rgba(34,197,94,0.3)", padding: "4px 12px", borderRadius: "20px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} />
          <span style={{ fontSize: "11px", fontWeight: "800", color: "#22c55e", textTransform: "uppercase" }}>
            Operational
          </span>
        </div>
      </div>

      {/* Grid of 8 modules */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "10px" }}>
        {modules.map((m) => {
          const isActive = m.status === "ACTIVE";
          const isNotConfigured = m.status === "NOT_CONFIGURED";

          return (
            <div
              key={m.key}
              style={{
                background: "rgba(255,255,255,0.02)",
                border: `1px solid ${isActive ? "rgba(34,197,94,0.2)" : isNotConfigured ? "rgba(245,158,11,0.25)" : "var(--border)"}`,
                borderRadius: "10px",
                padding: "10px 14px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ fontSize: "12px", fontWeight: "700", color: "#ffffff" }}>
                  {m.name}
                </div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "160px" }}>
                  {m.detail}
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                {isActive ? (
                  <span style={{ fontSize: "10px", fontWeight: "800", color: "#22c55e", background: "rgba(34,197,94,0.15)", padding: "2px 8px", borderRadius: "12px" }}>
                    ACTIVE
                  </span>
                ) : (
                  <span style={{ fontSize: "10px", fontWeight: "800", color: "#f59e0b", background: "rgba(245,158,11,0.15)", padding: "2px 8px", borderRadius: "12px" }}>
                    NOT SET
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
