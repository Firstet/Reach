"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  Activity,
  Calendar,
  CheckCircle2,
  Clock,
  Eye,
  Mail,
  MessageSquare,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  Users,
} from "lucide-react";

interface Campaign {
  id: string;
  name: string;
  status: string;
  target_industry: string | null;
  target_seniority: string | null;
  daily_send_limit: number;
  max_follow_ups: number;
  created_at: string;
}

const STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  draft: { bg: "rgba(90,90,114,0.2)", color: "#9090a8" },
  configured: { bg: "rgba(76,123,201,0.15)", color: "#4c7bc9" },
  active: { bg: "rgba(76,184,156,0.15)", color: "#4cb89c" },
  paused: { bg: "rgba(201,168,76,0.15)", color: "#c9a84c" },
  completed: { bg: "rgba(76,175,80,0.15)", color: "#4caf50" },
  archived: { bg: "rgba(90,90,114,0.15)", color: "#5a5a72" },
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [campaignStats, setCampaignStats] = useState<Record<string, any>>({});
  const [form, setForm] = useState({
    name: "",
    description: "",
    target_industry: "",
    target_seniority: "",
    value_proposition: "",
    discovery_query: "",
    approval_mode: "auto",
    min_score_threshold: 40,
    test_mode: false,
    daily_send_limit: 50,
    max_follow_ups: 3,
    follow_up_delay_hours: 72,
  });

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/campaigns?page_size=50");
      setCampaigns(data.items || []);
      setTotal(data.total || 0);

      // Fetch pipeline breakdown per campaign
      const pipelineSummary = await apiFetch("/api/v1/leads/pipeline/summary");
      setCampaignStats(pipelineSummary || {});
    } catch {
      /* API not yet connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/api/v1/campaigns", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setShowCreate(false);
      setForm({
        name: "",
        description: "",
        target_industry: "",
        target_seniority: "",
        value_proposition: "",
        discovery_query: "",
        approval_mode: "auto",
        min_score_threshold: 40,
        test_mode: false,
        daily_send_limit: 50,
        max_follow_ups: 3,
        follow_up_delay_hours: 72,
      });
      load();
    } catch (err) {
      alert("Failed to create campaign: " + err);
    }
  };

  const handleAction = async (id: string, action: "start" | "pause") => {
    try {
      await apiFetch(`/api/v1/campaigns/${id}/${action}`, { method: "POST" });
      load();
    } catch {
      alert(`Failed to ${action} campaign`);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: "var(--bg-secondary)",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    padding: "10px 12px",
    color: "var(--text-primary)",
    fontSize: "13px",
    outline: "none",
  };

  const labelStyle: React.CSSProperties = {
    display: "block",
    fontSize: "11px",
    fontWeight: "700",
    color: "var(--text-muted)",
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    marginBottom: "6px",
  };

  return (
    <div style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "22px", fontWeight: "900", letterSpacing: "-0.02em", color: "#ffffff", marginBottom: "4px" }}>
            RAYVEN AI Campaigns
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            {total} Active Autonomous Outreach Campaign{total !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          id="create-campaign-btn"
          onClick={() => setShowCreate(true)}
          style={{
            background: "var(--rayven-accent)",
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
          <Plus size={16} />
          Create New Campaign
        </button>
      </div>

      {/* Campaign list */}
      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading campaign operational states...
        </div>
      ) : campaigns.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "var(--bg-card)",
            border: "1px dashed var(--border)",
            borderRadius: "14px",
          }}
        >
          <Send size={40} style={{ color: "var(--rayven-accent)", marginBottom: "12px" }} />
          <h3 style={{ fontSize: "16px", fontWeight: "800", marginBottom: "8px", color: "#ffffff" }}>No campaigns configured</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            Create your first RayvenSC outreach campaign to automate discovery, personalization, and sending.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {campaigns.map((campaign) => {
            const isActive = campaign.status === "active";
            const statusStyle = STATUS_COLORS[campaign.status] || STATUS_COLORS.draft;

            // Operational stats per card
            const discovered = campaignStats["new"] || 0;
            const qualified = campaignStats["enriched"] || 0;
            const sent = campaignStats["outreach_sent"] || 0;
            const replies = campaignStats["replied"] || 0;
            const converted = campaignStats["converted"] || 0;

            return (
              <div
                key={campaign.id}
                style={{
                  background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
                  border: "1px solid var(--border)",
                  borderRadius: "14px",
                  padding: "24px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "18px",
                  boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
                }}
              >
                {/* Top Title Bar */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                      <h3 style={{ fontSize: "17px", fontWeight: "900", color: "#ffffff", margin: 0 }}>
                        {campaign.name}
                      </h3>
                      <span
                        style={{
                          ...statusStyle,
                          padding: "3px 12px",
                          borderRadius: "20px",
                          fontSize: "10px",
                          fontWeight: "800",
                          letterSpacing: "0.05em",
                          textTransform: "uppercase",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                        }}
                      >
                        <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: isActive ? "#22c55e" : "#f59e0b" }} />
                        {campaign.status}
                      </span>
                    </div>

                    <div style={{ display: "flex", gap: "18px", flexWrap: "wrap" }}>
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
                        <Users size={14} style={{ color: "var(--rayven-accent)" }} />
                        Audience: <strong>{campaign.target_industry || "Enterprise Execs"} ({campaign.target_seniority || "C-Level"})</strong>
                      </span>
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
                        <Mail size={14} style={{ color: "#38bdf8" }} />
                        Sending Limit: <strong>{campaign.daily_send_limit}/day</strong>
                      </span>
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
                        <RefreshCw size={14} style={{ color: "#a855f7" }} />
                        Follow-ups: <strong>{campaign.max_follow_ups} Steps</strong>
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      onClick={async () => {
                        try {
                          const res = await apiFetch("/api/v1/discovery/trigger", {
                            method: "POST",
                            body: JSON.stringify({ campaign_id: campaign.id }),
                          });
                          alert(`Discovery triggered! Job ID: ${res.job_id}`);
                        } catch (e) {
                          alert("Trigger failed: " + e);
                        }
                      }}
                      style={{
                        background: "rgba(56,189,248,0.12)",
                        border: "1px solid rgba(56,189,248,0.3)",
                        borderRadius: "8px",
                        padding: "8px 14px",
                        color: "#38bdf8",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <Search size={14} />
                      Discover Leads
                    </button>

                    {isActive ? (
                      <button
                        onClick={() => handleAction(campaign.id, "pause")}
                        style={{
                          background: "var(--rayven-accent-muted)",
                          border: "1px solid var(--rayven-accent)",
                          borderRadius: "8px",
                          padding: "8px 14px",
                          color: "var(--rayven-accent)",
                          fontSize: "12px",
                          fontWeight: "700",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <Pause size={14} />
                        Pause
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAction(campaign.id, "start")}
                        style={{
                          background: "rgba(34,197,94,0.15)",
                          border: "1px solid rgba(34,197,94,0.3)",
                          borderRadius: "8px",
                          padding: "8px 14px",
                          color: "#22c55e",
                          fontSize: "12px",
                          fontWeight: "700",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <Play size={14} />
                        Start Campaign
                      </button>
                    )}

                    <a
                      href="/dashboard/leads"
                      style={{
                        background: "rgba(255,255,255,0.03)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        padding: "8px 14px",
                        color: "#ffffff",
                        fontSize: "12px",
                        fontWeight: "700",
                        textDecoration: "none",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <Eye size={14} />
                      View Leads
                    </a>
                  </div>
                </div>

                {/* Real Operational Stats Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "10px", background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "10px", border: "1px solid var(--border)" }}>
                  <div>
                    <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Discovered
                    </div>
                    <div style={{ fontSize: "18px", fontWeight: "900", color: "#ffffff", marginTop: "2px" }}>
                      {discovered}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Qualified
                    </div>
                    <div style={{ fontSize: "18px", fontWeight: "900", color: "#22c55e", marginTop: "2px" }}>
                      {qualified}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Emails Sent
                    </div>
                    <div style={{ fontSize: "18px", fontWeight: "900", color: "var(--rayven-accent)", marginTop: "2px" }}>
                      {sent}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Replies
                    </div>
                    <div style={{ fontSize: "18px", fontWeight: "900", color: "#ec4899", marginTop: "2px" }}>
                      {replies}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Interested
                    </div>
                    <div style={{ fontSize: "18px", fontWeight: "900", color: "#a855f7", marginTop: "2px" }}>
                      {converted}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      Next Action
                    </div>
                    <div style={{ fontSize: "11px", fontWeight: "700", color: "#38bdf8", marginTop: "4px" }}>
                      {isActive ? "Auto Cadence" : "Paused"}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "24px",
          }}
          onClick={(e) => e.target === e.currentTarget && setShowCreate(false)}
        >
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "16px",
              padding: "32px",
              width: "100%",
              maxWidth: "560px",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <h2 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "24px" }}>
              New Campaign
            </h2>
            <form onSubmit={handleCreate}>
              {[
                { key: "name", label: "Campaign Name *", type: "text", required: true },
                { key: "description", label: "Description", type: "text" },
                { key: "target_industry", label: "Target Industry", type: "text", placeholder: "e.g. Technology, Healthcare" },
                { key: "target_seniority", label: "Target Seniority", type: "text", placeholder: "e.g. Director, VP, C-Level" },
                { key: "value_proposition", label: "Value Proposition", type: "textarea" },
              ].map(({ key, label, type, required, placeholder }) => (
                <div key={key} style={{ marginBottom: "16px" }}>
                  <label style={labelStyle}>{label}</label>
                  {type === "textarea" ? (
                    <textarea
                      value={(form as unknown as Record<string, string | number>)[key] as string}
                      onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                      placeholder={placeholder}
                      rows={3}
                      style={{ ...inputStyle, resize: "vertical" }}
                    />
                  ) : (
                    <input
                      type={type}
                      value={(form as unknown as Record<string, string | number>)[key] as string}
                      onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                      placeholder={placeholder}
                      required={required}
                      style={inputStyle}
                    />
                  )}
                </div>
              ))}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "24px" }}>
                <div>
                  <label style={labelStyle}>Daily Send Limit</label>
                  <input
                    type="number"
                    value={form.daily_send_limit}
                    onChange={(e) => setForm((f) => ({ ...f, daily_send_limit: +e.target.value }))}
                    min={1}
                    max={200}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Max Follow-ups</label>
                  <input
                    type="number"
                    value={form.max_follow_ups}
                    onChange={(e) => setForm((f) => ({ ...f, max_follow_ups: +e.target.value }))}
                    min={0}
                    max={10}
                    style={inputStyle}
                  />
                </div>
              </div>
              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  style={{
                    background: "transparent",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    padding: "10px 20px",
                    color: "var(--text-secondary)",
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  id="create-campaign-submit"
                  type="submit"
                  style={{
                    background: "linear-gradient(135deg, #c9a84c, #a87830)",
                    border: "none",
                    borderRadius: "8px",
                    padding: "10px 24px",
                    color: "#0a0a0f",
                    fontSize: "13px",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  Create Campaign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
