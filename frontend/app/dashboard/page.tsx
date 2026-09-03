"use client";

import { useEffect, useState } from "react";

interface Stats {
  campaigns: number;
  leads: number;
  conversations: number;
  escalated: number;
  pipeline: Record<string, number>;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  accent?: string;
  icon?: string;
}

function StatCard({ title, value, subtitle, accent, icon }: StatCardProps) {
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "20px 24px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {accent && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "2px",
            background: accent,
          }}
        />
      )}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div
            style={{
              fontSize: "11px",
              fontWeight: "600",
              color: "var(--text-muted)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              marginBottom: "8px",
            }}
          >
            {title}
          </div>
          <div
            style={{
              fontSize: "32px",
              fontWeight: "800",
              color: "var(--text-primary)",
              letterSpacing: "-0.02em",
              lineHeight: "1",
            }}
          >
            {value}
          </div>
          {subtitle && (
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "6px" }}>
              {subtitle}
            </div>
          )}
        </div>
        {icon && (
          <div
            style={{
              fontSize: "24px",
              opacity: 0.4,
              background: "var(--bg-hover)",
              width: "44px",
              height: "44px",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

const PIPELINE_STAGES = [
  { key: "new", label: "New", color: "#4c7bc9" },
  { key: "enriched", label: "Enriched", color: "#4caf50" },
  { key: "outreach_sent", label: "Outreach Sent", color: "#c9a84c" },
  { key: "follow_up", label: "Follow-up", color: "#9c88ff" },
  { key: "replied", label: "Replied", color: "#9c4cc9" },
  { key: "escalated", label: "Escalated", color: "#c94c4c" },
  { key: "converted", label: "Converted", color: "#4cb89c" },
];

async function apiFetch(path: string) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(path, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({
    campaigns: 0,
    leads: 0,
    conversations: 0,
    escalated: 0,
    pipeline: {},
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [campaigns, pipeline, conversations] = await Promise.all([
          apiFetch("/api/v1/campaigns?page_size=1"),
          apiFetch("/api/v1/leads/pipeline/summary"),
          apiFetch("/api/v1/conversations?page_size=1"),
        ]);
        const totalLeads = Object.values(pipeline as Record<string, number>).reduce(
          (a, b) => a + b, 0
        );
        setStats({
          campaigns: campaigns.total ?? 0,
          leads: totalLeads,
          conversations: conversations.total ?? 0,
          escalated: (pipeline as Record<string, number>)["escalated"] ?? 0,
          pipeline: pipeline,
        });
      } catch {
        // Stats will stay at 0 if API is not yet connected
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const totalLeads = Object.values(stats.pipeline).reduce((a, b) => a + b, 0);

  return (
    <div style={{ padding: "32px" }}>
      {/* Header */}
      <div style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
          <div
            style={{
              width: "4px",
              height: "24px",
              background: "linear-gradient(180deg, #c9a84c, #a87830)",
              borderRadius: "2px",
            }}
          />
          <h1
            style={{
              fontSize: "22px",
              fontWeight: "800",
              color: "var(--text-primary)",
              letterSpacing: "-0.02em",
            }}
          >
            Business Development Overview
          </h1>
        </div>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginLeft: "16px" }}>
          Rayven Strategic Communications · AI Outreach Intelligence
        </p>
      </div>

      {/* Top stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <StatCard
          title="Active Campaigns"
          value={loading ? "—" : stats.campaigns}
          subtitle="Configured campaigns"
          accent="linear-gradient(90deg, #c9a84c, #a87830)"
          icon="◈"
        />
        <StatCard
          title="Total Leads"
          value={loading ? "—" : totalLeads}
          subtitle="Across all campaigns"
          accent="linear-gradient(90deg, #4c7bc9, #3a60a0)"
          icon="◉"
        />
        <StatCard
          title="Conversations"
          value={loading ? "—" : stats.conversations}
          subtitle="Active threads"
          accent="linear-gradient(90deg, #4cb89c, #3a9080)"
          icon="◎"
        />
        <StatCard
          title="Needs Attention"
          value={loading ? "—" : stats.escalated}
          subtitle="Escalated to human"
          accent="linear-gradient(90deg, #c94c4c, #a03838)"
          icon="⚠"
        />
      </div>

      {/* Pipeline Funnel */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
          marginBottom: "24px",
        }}
      >
        <div
          style={{
            fontSize: "13px",
            fontWeight: "700",
            color: "var(--text-secondary)",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            marginBottom: "20px",
          }}
        >
          Lead Pipeline
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {PIPELINE_STAGES.map((stage) => {
            const count = stats.pipeline[stage.key] ?? 0;
            const pct = totalLeads > 0 ? (count / totalLeads) * 100 : 0;
            return (
              <div key={stage.key} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div
                  style={{
                    width: "100px",
                    fontSize: "12px",
                    color: "var(--text-secondary)",
                    flexShrink: 0,
                  }}
                >
                  {stage.label}
                </div>
                <div
                  style={{
                    flex: 1,
                    height: "6px",
                    background: "var(--bg-hover)",
                    borderRadius: "3px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${pct}%`,
                      height: "100%",
                      background: stage.color,
                      borderRadius: "3px",
                      transition: "width 0.8s ease",
                    }}
                  />
                </div>
                <div
                  style={{
                    width: "32px",
                    fontSize: "13px",
                    fontWeight: "700",
                    color: count > 0 ? "var(--text-primary)" : "var(--text-muted)",
                    textAlign: "right",
                    flexShrink: 0,
                  }}
                >
                  {count}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "24px",
        }}
      >
        <div
          style={{
            fontSize: "13px",
            fontWeight: "700",
            color: "var(--text-secondary)",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            marginBottom: "16px",
          }}
        >
          Quick Actions
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {[
            { href: "/dashboard/campaigns", label: "New Campaign", icon: "◈" },
            { href: "/dashboard/leads", label: "Add Leads", icon: "◉" },
            { href: "/dashboard/conversations?escalated=true", label: "View Escalated", icon: "⚠" },
            { href: "/dashboard/knowledge", label: "Knowledge Base", icon: "◫" },
            { href: "/dashboard/config", label: "Configure Providers", icon: "⚙" },
          ].map((action) => (
            <a
              key={action.href}
              href={action.href}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 16px",
                background: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                color: "var(--text-primary)",
                fontSize: "13px",
                fontWeight: "500",
                textDecoration: "none",
                transition: "all 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--accent-gold)";
                e.currentTarget.style.color = "var(--accent-gold)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.color = "var(--text-primary)";
              }}
            >
              <span>{action.icon}</span>
              {action.label}
            </a>
          ))}
        </div>
      </div>

      {/* Reach principle footer */}
      <div
        style={{
          marginTop: "32px",
          padding: "16px 20px",
          background: "rgba(201,168,76,0.05)",
          border: "1px solid rgba(201,168,76,0.15)",
          borderRadius: "8px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <div style={{ fontSize: "16px" }}>◈</div>
        <p style={{ fontSize: "12px", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: "1.5" }}>
          "Communication must be engineered, not improvised." — The Rayven Framework ·{" "}
          <span style={{ color: "var(--accent-gold)" }}>
            Reach generates relevant conversations, not spam.
          </span>
        </p>
      </div>
    </div>
  );
}
