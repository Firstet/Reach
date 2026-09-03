"use client";

import { useEffect, useState } from "react";

interface LeadItem {
  id: string;
  full_name: string;
  title: string;
  email: string;
  company_name: string;
  score: number | null;
  status: string;
  crm_stage: string;
  why_rayven: string | null;
  updated_at: string;
}

interface StageConfig {
  key: string;
  label: string;
  color: string;
}

async function apiFetch(path: string, opts?: RequestInit) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(path, {
    ...opts,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

import { Kanban, Sparkles, UserCheck, Users } from "lucide-react";

export default function CRMPage() {
  const [stages, setStages] = useState<StageConfig[]>([]);
  const [pipeline, setPipeline] = useState<Record<string, LeadItem[]>>({});
  const [totalLeads, setTotalLeads] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/crm/pipeline");
      setStages(data.stage_labels || []);
      setPipeline(data.pipeline || {});
      setTotalLeads(data.total_leads || 0);
    } catch {
      /* not connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleStageMove = async (leadId: string, newStage: string) => {
    try {
      await apiFetch(`/api/v1/crm/leads/${leadId}/stage`, {
        method: "PUT",
        body: JSON.stringify({ new_stage: newStage }),
      });
      load();
    } catch (e) {
      alert("Failed to move lead: " + e);
    }
  };

  return (
    <div style={{ padding: "32px", height: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "22px", fontWeight: "900", color: "#ffffff", letterSpacing: "-0.02em", marginBottom: "4px" }}>
            RAYVEN AI CRM Kanban Board
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            {totalLeads} Total Prospects Managed Across 12 Autonomous Conversion Stages
          </p>
        </div>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading CRM pipeline...
        </div>
      ) : (
        /* Kanban board across 12 stages */
        <div
          style={{
            display: "flex",
            gap: "12px",
            overflowX: "auto",
            flex: 1,
            paddingBottom: "12px",
          }}
        >
          {stages.map((stage) => {
            const items = pipeline[stage.key] || [];
            return (
              <div
                key={stage.key}
                style={{
                  minWidth: "240px",
                  width: "240px",
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  borderRadius: "12px",
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden",
                  flexShrink: 0,
                }}
              >
                {/* Column header */}
                <div
                  style={{
                    padding: "12px 14px",
                    borderBottom: "1px solid var(--border-subtle)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    borderTop: `3px solid ${stage.color}`,
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: "700", color: stage.color }}>
                    {stage.label}
                  </span>
                  <span
                    style={{
                      background: "var(--bg-hover)",
                      borderRadius: "20px",
                      padding: "1px 8px",
                      fontSize: "11px",
                      fontWeight: "700",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {items.length}
                  </span>
                </div>

                {/* Cards */}
                <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
                  {items.length === 0 ? (
                    <div
                      style={{
                        padding: "20px",
                        textAlign: "center",
                        color: "var(--text-muted)",
                        fontSize: "12px",
                        fontStyle: "italic",
                      }}
                    >
                      Empty
                    </div>
                  ) : (
                    items.map((lead) => (
                      <div
                        key={lead.id}
                        style={{
                          background: "var(--bg-card)",
                          border: `1px solid ${stage.key === "hot" ? "rgba(255,77,77,0.4)" : "var(--border)"}`,
                          borderRadius: "8px",
                          padding: "12px",
                          marginBottom: "8px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                          <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)" }}>
                            {lead.full_name}
                          </span>
                          {lead.score != null && (
                            <span style={{ fontSize: "10px", fontWeight: "700", color: lead.score >= 75 ? "#4cb89c" : "var(--text-muted)" }}>
                              {Math.round(lead.score)}pt
                            </span>
                          )}
                        </div>

                        <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginBottom: "6px" }}>
                          {lead.title} {lead.company_name ? `@ ${lead.company_name}` : ""}
                        </div>

                        {lead.why_rayven && (
                          <div style={{ fontSize: "10px", color: "var(--accent-gold)", marginBottom: "8px", lineHeight: "1.3" }}>
                            💡 {lead.why_rayven.slice(0, 70)}...
                          </div>
                        )}

                        {/* Move stage selector */}
                        <select
                          value={lead.crm_stage}
                          onChange={(e) => handleStageMove(lead.id, e.target.value)}
                          style={{
                            width: "100%",
                            background: "var(--bg-secondary)",
                            border: "1px solid var(--border)",
                            borderRadius: "6px",
                            padding: "4px 6px",
                            fontSize: "10px",
                            color: "var(--text-secondary)",
                            cursor: "pointer",
                          }}
                        >
                          {stages.map((s) => (
                            <option key={s.key} value={s.key}>
                              Move to: {s.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
