"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  BookOpen,
  CheckCircle2,
  Copy,
  Edit,
  Eye,
  FileText,
  Plus,
  Search,
  Send,
  Sparkles,
  Trash2,
  Zap,
} from "lucide-react";

interface Template {
  id: string;
  slug?: string;
  name: string;
  category: string;
  purpose: string;
  when_to_use: string;
  when_not_to_use: string;
  recommended_lead_types: string;
  subject_template: string;
  body_template: string;
  rules: string;
  tone: string;
  max_length: string;
  cta_style: string;
  follow_up_rules: string;
  is_active: boolean;
  variables: string[];
  rayven_capabilities: string[];
  created_at: string;
}

interface Campaign {
  id: string;
  name: string;
  status: string;
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals state
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);
  const [editTemplate, setEditTemplate] = useState<Template | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [assignModal, setAssignModal] = useState<Template | null>(null);
  const [selectedCampaignId, setSelectedCampaignId] = useState("");

  // AI Selection Engine state
  const [testerSignal, setTesterSignal] = useState("Founder with public speaking expertise at growing fintech");
  const [testerRole, setTesterRole] = useState("CEO / Founder");
  const [testingAi, setTestingAi] = useState(false);
  const [recommendationResult, setRecommendationResult] = useState<any | null>(null);

  // Form State for Create & Edit
  const [form, setForm] = useState({
    name: "",
    category: "Initial Outreach",
    purpose: "",
    when_to_use: "",
    when_not_to_use: "",
    recommended_lead_types: "",
    subject_template: "",
    body_template: "",
    rules: "",
    tone: "Consultative & Direct",
    max_length: "130 words",
    cta_style: "Low-pressure conversational",
    follow_up_rules: "",
    is_active: true,
    rayven_capabilities: "Strategic Communications, Narrative Architecture",
  });

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/templates?include_inactive=true");
      setTemplates(data.items || []);
    } catch (e) {
      console.error("Failed to load templates:", e);
    } finally {
      setLoading(false);
    }
  };

  const loadCampaigns = async () => {
    try {
      const data = await apiFetch("/api/v1/campaigns");
      setCampaigns(data.items || []);
      if (data.items?.length > 0) setSelectedCampaignId(data.items[0].id);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    loadTemplates();
    loadCampaigns();
  }, []);

  // Filtered Templates List
  const filteredTemplates = templates.filter((t) => {
    const matchesCategory =
      activeCategory === "all" ? true : t.category.toLowerCase() === activeCategory.toLowerCase();
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !query ||
      t.name.toLowerCase().includes(query) ||
      t.purpose.toLowerCase().includes(query) ||
      t.recommended_lead_types.toLowerCase().includes(query) ||
      (t.rayven_capabilities || []).some((c) => c.toLowerCase().includes(query));

    return matchesCategory && matchesSearch;
  });

  // Action Handlers
  const handleToggleActive = async (t: Template) => {
    try {
      const updated = await apiFetch(`/api/v1/templates/${t.id}/toggle`, { method: "POST" });
      setTemplates((prev) => prev.map((item) => (item.id === t.id ? updated : item)));
    } catch (e: any) {
      alert("Failed to toggle template: " + e.message);
    }
  };

  const handleDuplicate = async (t: Template) => {
    try {
      await apiFetch(`/api/v1/templates/${t.id}/duplicate`, { method: "POST" });
      await loadTemplates();
      alert(`Cloned framework: ${t.name} (Copy)`);
    } catch (e: any) {
      alert("Failed to duplicate template: " + e.message);
    }
  };

  const handleDelete = async (t: Template) => {
    if (!window.confirm(`Are you sure you want to delete template framework '${t.name}'?`)) return;
    try {
      await apiFetch(`/api/v1/templates/${t.id}`, { method: "DELETE" });
      await loadTemplates();
    } catch (e: any) {
      alert("Failed to delete template: " + e.message);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const caps = form.rayven_capabilities
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean);
      await apiFetch("/api/v1/templates", {
        method: "POST",
        body: JSON.stringify({ ...form, rayven_capabilities: caps }),
      });
      setShowCreate(false);
      resetForm();
      await loadTemplates();
      alert("Custom Strategic Framework Created!");
    } catch (e: any) {
      alert("Failed to create template: " + e.message);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTemplate) return;
    try {
      const caps = typeof form.rayven_capabilities === "string"
        ? form.rayven_capabilities.split(",").map((c) => c.trim()).filter(Boolean)
        : form.rayven_capabilities;

      const updated = await apiFetch(`/api/v1/templates/${editTemplate.id}`, {
        method: "PUT",
        body: JSON.stringify({ ...form, rayven_capabilities: caps }),
      });
      setEditTemplate(null);
      resetForm();
      setTemplates((prev) => prev.map((item) => (item.id === editTemplate.id ? updated : item)));
      alert("Framework Updated Successfully!");
    } catch (e: any) {
      alert("Failed to update template: " + e.message);
    }
  };

  const handleAssignToCampaign = async () => {
    if (!assignModal || !selectedCampaignId) return;
    try {
      await apiFetch(`/api/v1/templates/${assignModal.id}/assign-campaign?campaign_id=${selectedCampaignId}`, {
        method: "POST",
      });
      alert(`Framework '${assignModal.name}' attached to campaign!`);
      setAssignModal(null);
    } catch (e: any) {
      alert("Failed to assign template: " + e.message);
    }
  };

  const handleRunAiRecommendation = async () => {
    setTestingAi(true);
    setRecommendationResult(null);
    try {
      const res = await apiFetch("/api/v1/templates/recommend", {
        method: "POST",
        body: JSON.stringify({
          signal: testerSignal,
          job_title: testerRole,
          step_number: 1,
        }),
      });
      setRecommendationResult(res);
    } catch (e: any) {
      alert("AI recommendation error: " + e.message);
    } finally {
      setTestingAi(false);
    }
  };

  const openEditModal = (t: Template) => {
    setEditTemplate(t);
    setForm({
      name: t.name,
      category: t.category,
      purpose: t.purpose,
      when_to_use: t.when_to_use,
      when_not_to_use: t.when_not_to_use,
      recommended_lead_types: t.recommended_lead_types,
      subject_template: t.subject_template,
      body_template: t.body_template,
      rules: t.rules,
      tone: t.tone,
      max_length: t.max_length,
      cta_style: t.cta_style,
      follow_up_rules: t.follow_up_rules,
      is_active: t.is_active,
      rayven_capabilities: (t.rayven_capabilities || []).join(", "),
    });
  };

  const resetForm = () => {
    setForm({
      name: "",
      category: "Initial Outreach",
      purpose: "",
      when_to_use: "",
      when_not_to_use: "",
      recommended_lead_types: "",
      subject_template: "",
      body_template: "",
      rules: "",
      tone: "Consultative & Direct",
      max_length: "130 words",
      cta_style: "Low-pressure conversational",
      follow_up_rules: "",
      is_active: true,
      rayven_capabilities: "Strategic Communications, Narrative Architecture",
    });
  };

  return (
    <div style={{ padding: "32px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* Header Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "28px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span style={{ fontSize: "24px" }}>📚</span>
            <h1 style={{ fontSize: "22px", fontWeight: "900", letterSpacing: "-0.02em" }}>
              RayvenSC Strategic Outreach Playbook & Framework Library
            </h1>
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary, #9494a8)", maxWidth: "850px", lineHeight: "1.5" }}>
            15 Pre-populated Strategic Email Frameworks. These are <strong>not rigid word-for-word templates</strong>—they are strategic playbooks. The Rayven AI Agent uses the selected framework as a structural guide, then dynamically rewrites the message based on prospect research, company signals, and lead context.
          </p>
        </div>

        <button
          onClick={() => {
            resetForm();
            setShowCreate(true);
          }}
          style={{
            background: "linear-gradient(135deg, #c9a84c 0%, #a87830 100%)",
            color: "#0a0a0f",
            border: "none",
            borderRadius: "10px",
            padding: "12px 22px",
            fontSize: "13px",
            fontWeight: "800",
            cursor: "pointer",
            boxShadow: "0 4px 16px rgba(201, 168, 76, 0.25)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>➕</span> New Custom Framework
        </button>
      </div>

      {/* Interactive AI Template Selection Engine Simulator Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(201,168,76,0.12) 0%, rgba(18,12,30,0.85) 100%)",
          border: "1px solid rgba(201,168,76,0.3)",
          borderRadius: "16px",
          padding: "20px 24px",
          marginBottom: "32px",
          boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
          <span style={{ fontSize: "20px" }}>⚡</span>
          <h2 style={{ fontSize: "15px", fontWeight: "800", color: "#ffffff", margin: 0 }}>
            AI Template Selection Engine Simulator
          </h2>
          <span
            style={{
              fontSize: "10px",
              fontWeight: "800",
              color: "#c9a84c",
              background: "rgba(201,168,76,0.18)",
              padding: "3px 10px",
              borderRadius: "12px",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Automated Strategy Selector
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 220px 180px", gap: "12px", alignItems: "end" }}>
          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
              Prospect Signal / Business Research
            </label>
            <input
              type="text"
              value={testerSignal}
              onChange={(e) => setTesterSignal(e.target.value)}
              placeholder="e.g. Expanding into Kenya, launching new AI product, active keynote speaker..."
              style={{
                width: "100%",
                background: "rgba(0,0,0,0.4)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "10px 14px",
                color: "#ffffff",
                fontSize: "13px",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
              Job Title / Seniority
            </label>
            <input
              type="text"
              value={testerRole}
              onChange={(e) => setTesterRole(e.target.value)}
              placeholder="e.g. CEO, CMO, Founder"
              style={{
                width: "100%",
                background: "rgba(0,0,0,0.4)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "10px 14px",
                color: "#ffffff",
                fontSize: "13px",
              }}
            />
          </div>

          <button
            onClick={handleRunAiRecommendation}
            disabled={testingAi}
            style={{
              background: "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              padding: "10px 16px",
              fontSize: "12px",
              fontWeight: "800",
              cursor: testingAi ? "wait" : "pointer",
              height: "40px",
            }}
          >
            {testingAi ? "Analyzing..." : "⚡ Select Best Framework"}
          </button>
        </div>

        {/* Recommendation Result Display */}
        {recommendationResult && (
          <div
            style={{
              marginTop: "16px",
              background: "rgba(0,0,0,0.3)",
              border: "1px solid rgba(56,189,248,0.4)",
              borderRadius: "10px",
              padding: "14px 18px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ fontSize: "11px", fontWeight: "800", color: "#38bdf8", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                AI Recommendation Engine Result:
              </div>
              <div style={{ fontSize: "14px", fontWeight: "800", color: "#ffffff", marginTop: "2px" }}>
                🎯 Selected Framework: {recommendationResult.template?.name || recommendationResult.recommended_slug}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                {recommendationResult.rationale}
              </div>
            </div>
            {recommendationResult.template && (
              <button
                onClick={() => setPreviewTemplate(recommendationResult.template)}
                style={{
                  background: "rgba(201,168,76,0.2)",
                  border: "1px solid #c9a84c",
                  color: "#c9a84c",
                  borderRadius: "6px",
                  padding: "6px 14px",
                  fontSize: "12px",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                👁️ View Framework →
              </button>
            )}
          </div>
        )}
      </div>

      {/* Category Tabs & Search Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        {/* Category Tabs */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {[
            { id: "all", label: "All Frameworks (15)" },
            { id: "Initial Outreach", label: "Initial Outreach (11)" },
            { id: "Follow-up", label: "Follow-Up (3)" },
            { id: "Break-up", label: "Break-Up (1)" },
          ].map((tab) => {
            const isActive = activeCategory === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveCategory(tab.id)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  border: isActive ? "1px solid var(--accent-gold)" : "1px solid var(--border)",
                  background: isActive ? "rgba(201,168,76,0.15)" : "var(--bg-secondary, #12121c)",
                  color: isActive ? "var(--accent-gold)" : "var(--text-secondary)",
                  fontSize: "12px",
                  fontWeight: "700",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Search Bar */}
        <div style={{ width: "320px", position: "relative" }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search frameworks by keyword..."
            style={{
              width: "100%",
              background: "var(--bg-secondary, #12121c)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "8px 14px",
              color: "#ffffff",
              fontSize: "12px",
            }}
          />
        </div>
      </div>

      {/* Framework Grid */}
      {loading ? (
        <div style={{ padding: "64px", textAlign: "center", color: "var(--text-muted)" }}>
          Loading RayvenSC Strategic Framework Library...
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "var(--bg-card)",
            border: "1px dashed var(--border)",
            borderRadius: "16px",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>📑</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px", color: "#ffffff" }}>
            No framework templates match selected filter
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            Try resetting your search query or category filter.
          </p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))",
            gap: "20px",
          }}
        >
          {filteredTemplates.map((t) => {
            const isFollowUp = t.category === "Follow-up";
            const isBreakUp = t.category === "Break-up";

            const badgeBg = isFollowUp
              ? "rgba(168,85,247,0.15)"
              : isBreakUp
              ? "rgba(239,68,68,0.15)"
              : "rgba(201,168,76,0.15)";
            const badgeColor = isFollowUp ? "#c084fc" : isBreakUp ? "#f87171" : "#c9a84c";
            const badgeBorder = isFollowUp ? "#a855f7" : isBreakUp ? "#ef4444" : "#c9a84c";

            return (
              <div
                key={t.id}
                style={{
                  background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
                  border: `1px solid ${t.is_active ? "var(--border, #2a2a3c)" : "rgba(255,255,255,0.05)"}`,
                  borderRadius: "14px",
                  padding: "22px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  boxShadow: "0 8px 24px rgba(0,0,0,0.3)",
                  opacity: t.is_active ? 1 : 0.6,
                  transition: "all 0.2s ease",
                }}
              >
                <div>
                  {/* Category & Status Row */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <span
                      style={{
                        background: badgeBg,
                        color: badgeColor,
                        border: `1px solid ${badgeBorder}40`,
                        padding: "3px 10px",
                        borderRadius: "20px",
                        fontSize: "10px",
                        fontWeight: "800",
                        textTransform: "uppercase",
                        letterSpacing: "0.04em",
                      }}
                    >
                      {t.category}
                    </span>

                    {/* Active Toggle Switch */}
                    <button
                      onClick={() => handleToggleActive(t)}
                      style={{
                        background: t.is_active ? "rgba(16,185,129,0.15)" : "rgba(255,255,255,0.05)",
                        border: `1px solid ${t.is_active ? "rgba(16,185,129,0.3)" : "rgba(255,255,255,0.1)"}`,
                        color: t.is_active ? "#34d399" : "#94a3b8",
                        borderRadius: "12px",
                        padding: "3px 10px",
                        fontSize: "10px",
                        fontWeight: "700",
                        cursor: "pointer",
                      }}
                    >
                      {t.is_active ? "● ACTIVE" : "○ INACTIVE"}
                    </button>
                  </div>

                  {/* Title & Purpose */}
                  <h3 style={{ fontSize: "16px", fontWeight: "800", color: "#ffffff", marginBottom: "8px" }}>
                    {t.name}
                  </h3>
                  <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.5", marginBottom: "16px" }}>
                    {t.purpose}
                  </p>

                  {/* Recommended Lead Types */}
                  {t.recommended_lead_types && (
                    <div style={{ marginBottom: "12px" }}>
                      <span style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "4px" }}>
                        Target Profiles:
                      </span>
                      <span style={{ fontSize: "11px", color: "#e2e8f0", background: "rgba(255,255,255,0.04)", padding: "4px 8px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                        {t.recommended_lead_types}
                      </span>
                    </div>
                  )}

                  {/* Rayven Capabilities Tags */}
                  {t.rayven_capabilities && t.rayven_capabilities.length > 0 && (
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "16px" }}>
                      {t.rayven_capabilities.map((cap, i) => (
                        <span
                          key={i}
                          style={{
                            background: "rgba(56,189,248,0.12)",
                            color: "#38bdf8",
                            padding: "2px 8px",
                            borderRadius: "12px",
                            fontSize: "10px",
                            fontWeight: "700",
                          }}
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Card Action Footer */}
                <div style={{ borderTop: "1px solid var(--border)", paddingTop: "14px", marginTop: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      onClick={() => setPreviewTemplate(t)}
                      style={{
                        background: "rgba(201,168,76,0.15)",
                        border: "1px solid #c9a84c",
                        color: "#c9a84c",
                        borderRadius: "6px",
                        padding: "6px 12px",
                        fontSize: "11px",
                        fontWeight: "700",
                        cursor: "pointer",
                      }}
                    >
                      👁️ Preview
                    </button>
                    <button
                      onClick={() => setAssignModal(t)}
                      style={{
                        background: "rgba(56,189,248,0.15)",
                        border: "1px solid #38bdf8",
                        color: "#38bdf8",
                        borderRadius: "6px",
                        padding: "6px 12px",
                        fontSize: "11px",
                        fontWeight: "700",
                        cursor: "pointer",
                      }}
                    >
                      🚀 Use Template
                    </button>
                  </div>

                  <div style={{ display: "flex", gap: "6px" }}>
                    <button
                      onClick={() => openEditModal(t)}
                      title="Edit Framework"
                      style={{ background: "transparent", border: "1px solid var(--border)", color: "#94a3b8", borderRadius: "6px", padding: "6px 8px", fontSize: "11px", cursor: "pointer" }}
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => handleDuplicate(t)}
                      title="Duplicate Framework"
                      style={{ background: "transparent", border: "1px solid var(--border)", color: "#94a3b8", borderRadius: "6px", padding: "6px 8px", fontSize: "11px", cursor: "pointer" }}
                    >
                      📋
                    </button>
                    {t.slug && !t.slug.startsWith("strategic_") && (
                      <button
                        onClick={() => handleDelete(t)}
                        title="Delete Framework"
                        style={{ background: "transparent", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", borderRadius: "6px", padding: "6px 8px", fontSize: "11px", cursor: "pointer" }}
                      >
                        🗑️
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 1. Rich Preview Drawer Modal */}
      {previewTemplate && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(5, 7, 12, 0.85)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "24px",
          }}
        >
          <div
            style={{
              background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
              border: "1px solid rgba(201, 168, 76, 0.3)",
              borderRadius: "16px",
              padding: "28px",
              maxWidth: "760px",
              width: "100%",
              maxHeight: "85vh",
              overflowY: "auto",
              boxShadow: "0 24px 48px rgba(0, 0, 0, 0.8)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", borderBottom: "1px solid var(--border)", paddingBottom: "16px" }}>
              <div>
                <span style={{ fontSize: "11px", fontWeight: "800", color: "#c9a84c", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {previewTemplate.category}
                </span>
                <h2 style={{ fontSize: "20px", fontWeight: "900", color: "#ffffff", marginTop: "2px" }}>
                  {previewTemplate.name}
                </h2>
              </div>
              <button
                onClick={() => setPreviewTemplate(null)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "22px", cursor: "pointer" }}
              >
                ×
              </button>
            </div>

            {/* Framework Details */}
            <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
              <div>
                <h4 style={{ fontSize: "11px", fontWeight: "800", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                  Strategic Purpose & Approach
                </h4>
                <p style={{ fontSize: "13px", color: "#e2e8f0", lineHeight: "1.5" }}>{previewTemplate.purpose}</p>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "10px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", fontWeight: "800", color: "#34d399", textTransform: "uppercase", marginBottom: "4px" }}>
                    WHEN TO USE:
                  </div>
                  <div style={{ fontSize: "12px", color: "#e2e8f0", lineHeight: "1.4" }}>{previewTemplate.when_to_use}</div>
                </div>

                <div style={{ background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: "10px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", fontWeight: "800", color: "#f87171", textTransform: "uppercase", marginBottom: "4px" }}>
                    WHEN NOT TO USE:
                  </div>
                  <div style={{ fontSize: "12px", color: "#e2e8f0", lineHeight: "1.4" }}>{previewTemplate.when_not_to_use}</div>
                </div>
              </div>

              {/* Subject & Body Framework */}
              <div style={{ background: "rgba(201,168,76,0.06)", border: "1px solid rgba(201,168,76,0.25)", borderRadius: "12px", padding: "18px" }}>
                <div style={{ fontSize: "11px", fontWeight: "800", color: "#c9a84c", textTransform: "uppercase", marginBottom: "6px" }}>
                  Subject Pattern:
                </div>
                <div style={{ fontSize: "13px", fontWeight: "700", color: "#ffffff", marginBottom: "14px", fontFamily: "monospace" }}>
                  {previewTemplate.subject_template}
                </div>

                <div style={{ fontSize: "11px", fontWeight: "800", color: "#c9a84c", textTransform: "uppercase", marginBottom: "6px" }}>
                  Message Body Framework:
                </div>
                <div
                  style={{
                    fontSize: "13px",
                    color: "#e2e8f0",
                    lineHeight: "1.6",
                    whiteSpace: "pre-wrap",
                    background: "rgba(0,0,0,0.3)",
                    padding: "16px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                  }}
                >
                  {previewTemplate.body_template}
                </div>
              </div>

              {/* Rules & Constraints */}
              <div>
                <h4 style={{ fontSize: "11px", fontWeight: "800", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  AI Writing Rules & Constraints:
                </h4>
                <div style={{ fontSize: "12px", color: "#94a3b8", whiteSpace: "pre-wrap", lineHeight: "1.5", background: "rgba(255,255,255,0.03)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                  {previewTemplate.rules}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "24px" }}>
              <button
                onClick={() => setPreviewTemplate(null)}
                style={{ background: "transparent", border: "1px solid var(--border)", color: "#94a3b8", borderRadius: "8px", padding: "10px 18px", fontSize: "13px", cursor: "pointer" }}
              >
                Close Preview
              </button>
              <button
                onClick={() => {
                  setAssignModal(previewTemplate);
                  setPreviewTemplate(null);
                }}
                style={{
                  background: "linear-gradient(135deg, #c9a84c 0%, #a87830 100%)",
                  color: "#0a0a0f",
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 22px",
                  fontSize: "13px",
                  fontWeight: "800",
                  cursor: "pointer",
                }}
              >
                Use in Campaign →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Assign Framework to Campaign Modal */}
      {assignModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(5, 7, 12, 0.85)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "24px",
          }}
        >
          <div
            style={{
              background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
              border: "1px solid rgba(201, 168, 76, 0.3)",
              borderRadius: "16px",
              padding: "28px",
              maxWidth: "500px",
              width: "100%",
            }}
          >
            <h3 style={{ fontSize: "17px", fontWeight: "800", color: "#ffffff", marginBottom: "8px" }}>
              Attach Framework to Campaign
            </h3>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "20px" }}>
              Framework: <strong>{assignModal.name}</strong>
            </p>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                Select Active Campaign
              </label>
              <select
                value={selectedCampaignId}
                onChange={(e) => setSelectedCampaignId(e.target.value)}
                style={{
                  width: "100%",
                  background: "var(--bg-secondary, #12121c)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "10px 12px",
                  color: "#ffffff",
                  fontSize: "13px",
                }}
              >
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.status})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                onClick={() => setAssignModal(null)}
                style={{ background: "transparent", border: "1px solid var(--border)", color: "#94a3b8", borderRadius: "8px", padding: "10px 16px", fontSize: "13px", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                onClick={handleAssignToCampaign}
                style={{
                  background: "linear-gradient(135deg, #c9a84c 0%, #a87830 100%)",
                  color: "#0a0a0f",
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 20px",
                  fontSize: "13px",
                  fontWeight: "800",
                  cursor: "pointer",
                }}
              >
                Confirm Assignment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. Create / Edit Framework Modal */}
      {(showCreate || editTemplate) && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(5, 7, 12, 0.85)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "24px",
          }}
        >
          <div
            style={{
              background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
              border: "1px solid rgba(201, 168, 76, 0.3)",
              borderRadius: "16px",
              padding: "28px",
              maxWidth: "680px",
              width: "100%",
              maxHeight: "88vh",
              overflowY: "auto",
            }}
          >
            <h2 style={{ fontSize: "18px", fontWeight: "900", color: "#ffffff", marginBottom: "20px" }}>
              {editTemplate ? `Edit Framework: ${editTemplate.name}` : "Create Custom Strategic Framework"}
            </h2>

            <form onSubmit={editTemplate ? handleEditSubmit : handleCreateSubmit}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                    Framework Name *
                  </label>
                  <input
                    required
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px" }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                    Category *
                  </label>
                  <select
                    value={form.category}
                    onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px" }}
                  >
                    <option value="Initial Outreach">Initial Outreach</option>
                    <option value="Follow-up">Follow-up</option>
                    <option value="Break-up">Break-up</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  Strategic Purpose & Objective
                </label>
                <textarea
                  rows={2}
                  value={form.purpose}
                  onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))}
                  placeholder="Explain the high-level purpose of this framework..."
                  style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px", resize: "vertical" }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                    When to Use
                  </label>
                  <input
                    value={form.when_to_use}
                    onChange={(e) => setForm((f) => ({ ...f, when_to_use: e.target.value }))}
                    placeholder="Growth, new market entry, founder speaking..."
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px" }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                    When NOT to Use
                  </label>
                  <input
                    value={form.when_not_to_use}
                    onChange={(e) => setForm((f) => ({ ...f, when_not_to_use: e.target.value }))}
                    placeholder="Generic research, unverified claims..."
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px" }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  Subject Line Framework *
                </label>
                <input
                  required
                  value={form.subject_template}
                  onChange={(e) => setForm((f) => ({ ...f, subject_template: e.target.value }))}
                  placeholder="A thought on {{company}}'s {{strategic_opportunity}}"
                  style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px", fontFamily: "monospace" }}
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  Message Body Framework Structure *
                </label>
                <textarea
                  required
                  rows={5}
                  value={form.body_template}
                  onChange={(e) => setForm((f) => ({ ...f, body_template: e.target.value }))}
                  placeholder="Hi {{first_name}}, ..."
                  style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px", resize: "vertical" }}
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  Strategic Writing Rules & Constraints
                </label>
                <textarea
                  rows={3}
                  value={form.rules}
                  onChange={(e) => setForm((f) => ({ ...f, rules: e.target.value }))}
                  placeholder="- Never generic compliments&#10;- Specific observation required"
                  style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "#ffffff", fontSize: "13px", resize: "vertical" }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "20px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                    Tone
                  </label>
                  <input
                    value={form.tone}
                    onChange={(e) => setForm((f) => ({ ...f, tone: e.target.value }))}
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px 10px", color: "#ffffff", fontSize: "12px" }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                    Max Length
                  </label>
                  <input
                    value={form.max_length}
                    onChange={(e) => setForm((f) => ({ ...f, max_length: e.target.value }))}
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px 10px", color: "#ffffff", fontSize: "12px" }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                    CTA Style
                  </label>
                  <input
                    value={form.cta_style}
                    onChange={(e) => setForm((f) => ({ ...f, cta_style: e.target.value }))}
                    style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px 10px", color: "#ffffff", fontSize: "12px" }}
                  />
                </div>
              </div>

              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreate(false);
                    setEditTemplate(null);
                  }}
                  style={{ background: "transparent", border: "1px solid var(--border)", color: "#94a3b8", borderRadius: "8px", padding: "10px 18px", fontSize: "13px", cursor: "pointer" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    background: "linear-gradient(135deg, #c9a84c 0%, #a87830 100%)",
                    color: "#0a0a0f",
                    border: "none",
                    borderRadius: "8px",
                    padding: "10px 22px",
                    fontSize: "13px",
                    fontWeight: "800",
                    cursor: "pointer",
                  }}
                >
                  {editTemplate ? "Save Framework Changes" : "Create Framework"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
