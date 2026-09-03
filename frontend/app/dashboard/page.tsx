"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Flame,
  Kanban,
  Mail,
  MessageSquare,
  Plus,
  Send,
  Settings,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import AutomationEngineStatus from "../components/AutomationEngineStatus";

interface Stats {
  campaigns: number;
  leads: number;
  conversations: number;
  escalated: number;
  sent_emails: number;
  replies: number;
  pipeline: Record<string, number>;
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  accent?: string;
  icon?: any;
}

function StatCard({ title, value, subtitle, accent, icon: Icon }: StatCardProps) {
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "14px",
        padding: "20px 24px",
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
      }}
    >
      {accent && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "3px",
            background: accent,
          }}
        />
      )}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div
            style={{
              fontSize: "11px",
              fontWeight: "700",
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
              fontWeight: "900",
              color: "#ffffff",
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
        {Icon && (
          <div
            style={{
              background: "var(--rayven-accent-muted)",
              color: "var(--rayven-accent)",
              width: "44px",
              height: "44px",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Icon size={22} />
          </div>
        )}
      </div>
    </div>
  );
}

const PIPELINE_STAGES = [
  { key: "new", label: "New Leads", color: "#38bdf8" },
  { key: "enriched", label: "Enriched", color: "#22c55e" },
  { key: "outreach_sent", label: "Outreach Sent", color: "var(--rayven-accent)" },
  { key: "follow_up", label: "Follow-up", color: "#a855f7" },
  { key: "replied", label: "Replied", color: "#ec4899" },
  { key: "escalated", label: "Escalated", color: "#ef4444" },
  { key: "converted", label: "Converted", color: "#10b981" },
];

async function apiFetch(path: string, options?: RequestInit) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(path, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...((options?.headers as Record<string, string>) || {}),
    },
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
    sent_emails: 0,
    replies: 0,
    pipeline: {},
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [campaigns, pipeline, conversations, dailyLogs] = await Promise.all([
          apiFetch("/api/v1/campaigns?page_size=1"),
          apiFetch("/api/v1/leads/pipeline/summary"),
          apiFetch("/api/v1/conversations?page_size=1"),
          apiFetch("/api/v1/conversations/daily-outreach-logs"),
        ]);
        const totalLeads = Object.values(pipeline as Record<string, number>).reduce(
          (a, b) => a + b, 0
        );

        let totalSent = 0;
        let totalReplies = 0;
        if (dailyLogs?.dates) {
          for (const d of dailyLogs.dates) {
            totalSent += d.total_sent || 0;
            totalReplies += d.total_replies || 0;
          }
        }

        setStats({
          campaigns: campaigns.total ?? 0,
          leads: totalLeads,
          conversations: conversations.total ?? 0,
          escalated: (pipeline as Record<string, number>)["escalated"] ?? 0,
          sent_emails: totalSent,
          replies: totalReplies,
          pipeline: pipeline,
        });
      } catch {
        // Stats stay at real 0
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const totalLeads = Object.values(stats.pipeline).reduce((a, b) => a + b, 0);

  return (
    <div style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "6px" }}>
            <div
              style={{
                width: "4px",
                height: "26px",
                background: "var(--rayven-accent)",
                borderRadius: "2px",
                boxShadow: "0 0 10px var(--rayven-accent-glow)",
              }}
            />
            <h1
              style={{
                fontSize: "24px",
                fontWeight: "900",
                color: "#ffffff",
                letterSpacing: "-0.02em",
              }}
            >
              RAYVEN AI — Business Development Operating System
            </h1>
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginLeft: "16px" }}>
            Rayven Strategic Communications · Autonomous Enterprise Outreach & Personalization Platform
          </p>
        </div>

        <button
          onClick={async () => {
            try {
              const res = await apiFetch("/api/v1/outreach/trigger-tick", { method: "POST" });
              alert(`⚡ Outreach Cycle Triggered!\nLeads Advanced: ${res.stats?.leads_advanced || 0}\nMessages Sent: ${res.stats?.messages_sent || 0}`);
            } catch (e) {
              alert("Failed to trigger cycle: " + e);
            }
          }}
          style={{
            background: "linear-gradient(135deg, var(--rayven-accent), #c87a0c)",
            color: "#ffffff",
            border: "none",
            borderRadius: "10px",
            padding: "10px 20px",
            fontSize: "13px",
            fontWeight: "800",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "0 0 16px var(--rayven-accent-glow)",
          }}
        >
          <Send size={16} />
          Trigger Automated Outreach Now
        </button>
      </div>

      {/* Real-time Automation Engine Status Widget */}
      <AutomationEngineStatus />

      {/* Operational Stats Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
        }}
      >
        <StatCard
          title="Active Campaigns"
          value={loading ? "0" : stats.campaigns}
          subtitle="Configured campaigns"
          accent="linear-gradient(90deg, var(--rayven-accent), #c87a0c)"
          icon={Send}
        />
        <StatCard
          title="Total Prospect Leads"
          value={loading ? "0" : totalLeads}
          subtitle="Discovered enterprise leads"
          accent="linear-gradient(90deg, #38bdf8, #0284c7)"
          icon={Users}
        />
        <StatCard
          title="Emails Sent Out"
          value={loading ? "0" : stats.sent_emails}
          subtitle="Verified outbound dispatches"
          accent="linear-gradient(90deg, #a855f7, #7e22ce)"
          icon={Mail}
        />
        <StatCard
          title="Prospect Replies"
          value={loading ? "0" : stats.replies}
          subtitle="Inbound engagement"
          accent="linear-gradient(90deg, #ec4899, #be185d)"
          icon={MessageSquare}
        />
        <StatCard
          title="Escalated Threads"
          value={loading ? "0" : stats.escalated}
          subtitle="Human operator handoffs"
          accent="linear-gradient(90deg, #ef4444, #b91c1c)"
          icon={AlertTriangle}
        />
      </div>

      {/* Pipeline Funnel */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "14px",
          padding: "24px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div
            style={{
              fontSize: "13px",
              fontWeight: "800",
              color: "var(--text-secondary)",
              letterSpacing: "0.06em",
              textTransform: "uppercase",
            }}
          >
            Lead Pipeline Funnel
          </div>
          <div style={{ fontSize: "12px", color: "var(--rayven-accent)", fontWeight: "700" }}>
            Total Pipeline Volume: {totalLeads}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {PIPELINE_STAGES.map((stage) => {
            const count = stats.pipeline[stage.key] ?? 0;
            const pct = totalLeads > 0 ? (count / totalLeads) * 100 : 0;
            return (
              <div key={stage.key} style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                <div
                  style={{
                    width: "120px",
                    fontSize: "13px",
                    fontWeight: "600",
                    color: "var(--text-secondary)",
                    flexShrink: 0,
                  }}
                >
                  {stage.label}
                </div>
                <div
                  style={{
                    flex: 1,
                    height: "8px",
                    background: "rgba(255,255,255,0.04)",
                    borderRadius: "4px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${pct}%`,
                      height: "100%",
                      background: stage.color,
                      borderRadius: "4px",
                      transition: "width 0.8s ease",
                      boxShadow: `0 0 10px ${stage.color}40`,
                    }}
                  />
                </div>
                <div
                  style={{
                    width: "40px",
                    fontSize: "13px",
                    fontWeight: "800",
                    color: count > 0 ? "#ffffff" : "var(--text-muted)",
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
          borderRadius: "14px",
          padding: "24px",
        }}
      >
        <div
          style={{
            fontSize: "13px",
            fontWeight: "800",
            color: "var(--text-secondary)",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            marginBottom: "16px",
          }}
        >
          Quick Control Actions
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {[
            { href: "/dashboard/campaigns", label: "Create Campaign", icon: Plus },
            { href: "/dashboard/leads", label: "Discover Leads", icon: Users },
            { href: "/dashboard/conversations?escalated=true", label: "View Escalated", icon: AlertTriangle },
            { href: "/dashboard/knowledge", label: "Knowledge Base", icon: BookOpen },
            { href: "/dashboard/config", label: "Provider Settings", icon: Settings },
          ].map((action) => {
            const Icon = action.icon;
            return (
              <a
                key={action.href}
                href={action.href}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "9px",
                  padding: "10px 18px",
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  borderRadius: "10px",
                  color: "#ffffff",
                  fontSize: "13px",
                  fontWeight: "700",
                  textDecoration: "none",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--rayven-accent)";
                  e.currentTarget.style.color = "var(--rayven-accent)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.color = "#ffffff";
                }}
              >
                <Icon size={16} />
                {action.label}
              </a>
            );
          })}
        </div>
      </div>

      {/* Rayven principle footer */}
      <div
        style={{
          padding: "16px 20px",
          background: "var(--rayven-accent-muted)",
          border: "1px solid var(--rayven-accent-glow)",
          borderRadius: "10px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <Sparkles size={18} style={{ color: "var(--rayven-accent)", flexShrink: 0 }} />
        <p style={{ fontSize: "12px", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: "1.5", margin: 0 }}>
          "Communication must be engineered, not improvised." — The Rayven Framework ·{" "}
          <span style={{ color: "var(--rayven-accent)", fontWeight: "700" }}>
            RAYVEN AI generates high-converting, peer-level executive conversations.
          </span>
        </p>
      </div>
    </div>
  );
}

