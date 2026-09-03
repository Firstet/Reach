"use client";

import { useEffect, useState } from "react";

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

async function apiFetch(path: string, options?: RequestInit) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...((options?.headers as Record<string, string>) || {}),
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
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
      setCampaigns(data.items);
      setTotal(data.total);
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
    fontWeight: "600",
    color: "var(--text-muted)",
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    marginBottom: "6px",
  };

  return (
    <div style={{ padding: "32px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "20px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px" }}>
            Campaigns
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            {total} campaign{total !== 1 ? "s" : ""} configured
          </p>
        </div>
        <button
          id="create-campaign-btn"
          onClick={() => setShowCreate(true)}
          style={{
            background: "linear-gradient(135deg, #c9a84c, #a87830)",
            color: "#0a0a0f",
            border: "none",
            borderRadius: "8px",
            padding: "10px 20px",
            fontSize: "13px",
            fontWeight: "700",
            cursor: "pointer",
          }}
        >
          + New Campaign
        </button>
      </div>

      {/* Campaign list */}
      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading campaigns...
        </div>
      ) : campaigns.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "var(--bg-card)",
            border: "1px dashed var(--border)",
            borderRadius: "12px",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>◈</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>No campaigns yet</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            Create your first outreach campaign to start reaching qualified prospects.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {campaigns.map((campaign) => {
            const statusStyle = STATUS_COLORS[campaign.status] || STATUS_COLORS.draft;
            return (
              <div
                key={campaign.id}
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "12px",
                  padding: "20px 24px",
                  display: "flex",
                  alignItems: "center",
                  gap: "16px",
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                    <h3 style={{ fontSize: "15px", fontWeight: "700" }}>{campaign.name}</h3>
                    <span
                      style={{
                        ...statusStyle,
                        padding: "2px 8px",
                        borderRadius: "20px",
                        fontSize: "10px",
                        fontWeight: "700",
                        letterSpacing: "0.05em",
                        textTransform: "uppercase",
                      }}
                    >
                      {campaign.status}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
                    {campaign.target_industry && (
                      <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                        📍 {campaign.target_industry}
                      </span>
                    )}
                    <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                      📧 {campaign.daily_send_limit}/day
                    </span>
                    <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                      🔄 {campaign.max_follow_ups} follow-ups
                    </span>
                  </div>
                </div>
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
                      background: "rgba(76,123,201,0.15)",
                      border: "1px solid rgba(76,123,201,0.3)",
                      borderRadius: "7px",
                      padding: "7px 14px",
                      color: "#4c7bc9",
                      fontSize: "12px",
                      fontWeight: "600",
                      cursor: "pointer",
                    }}
                  >
                    🔍 Discover Leads
                  </button>
                  {campaign.status !== "active" && (
                    <button
                      onClick={() => handleAction(campaign.id, "start")}
                      style={{
                        background: "rgba(76,184,156,0.15)",
                        border: "1px solid rgba(76,184,156,0.3)",
                        borderRadius: "7px",
                        padding: "7px 14px",
                        color: "#4cb89c",
                        fontSize: "12px",
                        fontWeight: "600",
                        cursor: "pointer",
                      }}
                    >
                      Start
                    </button>
                  )}
                  {campaign.status === "active" && (
                    <button
                      onClick={() => handleAction(campaign.id, "pause")}
                      style={{
                        background: "rgba(201,168,76,0.12)",
                        border: "1px solid rgba(201,168,76,0.3)",
                        borderRadius: "7px",
                        padding: "7px 14px",
                        color: "#c9a84c",
                        fontSize: "12px",
                        fontWeight: "600",
                        cursor: "pointer",
                      }}
                    >
                      Pause
                    </button>
                  )}
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
