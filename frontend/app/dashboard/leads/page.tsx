"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  FileText,
  Filter,
  Mail,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  UserCheck,
  UserRound,
  Users,
} from "lucide-react";

const STATUS_CONFIG: Record<string, { label: string; bg: string; color: string; border: string }> = {
  new: { label: "New Lead", bg: "rgba(56,189,248,0.12)", color: "#38bdf8", border: "rgba(56,189,248,0.3)" },
  discovered: { label: "Discovered", bg: "rgba(56,189,248,0.12)", color: "#38bdf8", border: "rgba(56,189,248,0.3)" },
  enriched: { label: "Enriched", bg: "rgba(34,197,94,0.12)", color: "#22c55e", border: "rgba(34,197,94,0.3)" },
  researched: { label: "Researched", bg: "rgba(245,158,11,0.12)", color: "#f59e0b", border: "rgba(245,158,11,0.3)" },
  scored: { label: "Scored", bg: "rgba(245,158,11,0.12)", color: "#f59e0b", border: "rgba(245,158,11,0.3)" },
  qualified: { label: "Qualified", bg: "var(--rayven-accent-muted)", color: "var(--rayven-accent)", border: "rgba(224,140,24,0.4)" },
  outreach_pending: { label: "Outreach Pending", bg: "rgba(168,85,247,0.12)", color: "#a855f7", border: "rgba(168,85,247,0.3)" },
  outreach_sent: { label: "Outreach Sent", bg: "rgba(168,85,247,0.15)", color: "#c084fc", border: "rgba(168,85,247,0.4)" },
  follow_up: { label: "Follow-up Scheduled", bg: "rgba(236,72,153,0.15)", color: "#f472b6", border: "rgba(236,72,153,0.4)" },
  delivered: { label: "Delivered", bg: "rgba(34,197,94,0.15)", color: "#22c55e", border: "rgba(34,197,94,0.4)" },
  replied: { label: "Replied", bg: "rgba(56,189,248,0.15)", color: "#38bdf8", border: "rgba(56,189,248,0.4)" },
  escalated: { label: "Needs Human Handoff", bg: "rgba(239,68,68,0.18)", color: "#f87171", border: "rgba(239,68,68,0.4)" },
  human_engaged: { label: "Human Engaged", bg: "rgba(249,115,22,0.18)", color: "#fb923c", border: "rgba(249,115,22,0.4)" },
  converted: { label: "Converted Client", bg: "var(--rayven-accent-muted)", color: "var(--rayven-accent)", border: "var(--rayven-accent)" },
  not_interested: { label: "Not Interested", bg: "rgba(100,116,139,0.12)", color: "#94a3b8", border: "rgba(100,116,139,0.3)" },
};

interface ProspectInfo {
  first_name?: string;
  last_name?: string;
  full_name?: string;
  email?: string;
  email_confidence?: number;
  email_verified?: boolean;
  phone?: string;
  contact?: string;
  title?: string;
  designation?: string;
  position?: string;
  department?: string;
  linkedin_url?: string;
  company_name?: string;
  company_domain?: string;
  company_industry?: string;
}

interface Lead {
  id: string;
  status: string;
  crm_stage: string;
  outreach_count: number;
  reply_count: number;
  needs_human_service: boolean;
  discovery_source: string;
  prospect?: ProspectInfo;
  score?: { total: number; is_qualified: boolean };
  created_at: string;
}


export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState("all");
  const [scrapingQuery, setScrapingQuery] = useState(
    "CEOs, CMOs and Marketing Directors at Nigerian technology, finance and healthcare companies"
  );
  const [scrapingMaxResults, setScrapingMaxResults] = useState(10);
  const [scraping, setScraping] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [leadMessages, setLeadMessages] = useState<any[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const loadLeads = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await apiFetch("/api/v1/leads?page_size=100");
      setLeads(data.items || []);
    } catch {
      /* not connected */
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads(true);
    // Auto refresh every 10 seconds to update scraped leads count dynamically
    const interval = setInterval(() => {
      loadLeads(false);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedLead) {
      setLoadingMessages(true);
      apiFetch(`/api/v1/conversations/lead/${selectedLead.id}`)
        .then((data) => {
          setLeadMessages(data.messages || []);
        })
        .catch(() => setLeadMessages([]))
        .finally(() => setLoadingMessages(false));
    } else {
      setLeadMessages([]);
    }
  }, [selectedLead]);

  const handleTestScraping = async (e: React.FormEvent) => {
    e.preventDefault();
    setScraping(true);
    try {
      const res = await apiFetch("/api/v1/leads/test-scraping", {
        method: "POST",
        body: JSON.stringify({ query: scrapingQuery, max_results: scrapingMaxResults }),
      });
      alert(`🎉 Web Scraping Engine Executed!\nExtracted and enrolled ${res.scraped_count} leads matching query.`);
      await loadLeads();
    } catch (err: any) {
      alert("Scraping test error: " + (err?.message || err));
    } finally {
      setScraping(false);
    }
  };

  const filteredLeads = leads.filter((l) => {
    if (activeFilter === "human") return l.needs_human_service;
    if (activeFilter === "new") return l.status === "new" || l.status === "discovered";
    if (activeFilter === "outreach") return l.status === "outreach_sent" || l.status === "follow_up";
    if (activeFilter === "replied") return l.status === "replied" || l.reply_count > 0;
    return true;
  });

  return (
    <div style={{ padding: "32px", maxWidth: "1350px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 style={{ fontSize: "22px", fontWeight: "900", letterSpacing: "-0.02em", marginBottom: "6px" }}>
              Lead Repository Storage Vault & Auto-Discovery Pipeline
            </h1>
            <p style={{ fontSize: "13px", color: "var(--text-secondary, #9494a8)", lineHeight: "1.5" }}>
              Central database repository storing all scraped executive prospects, email verifications, and outreach sequences.
            </p>
          </div>

          {/* Automatic Scraping Schedule Status Badge */}
          <div style={{ background: "rgba(201,168,76,0.12)", border: "1px solid rgba(201,168,76,0.3)", borderRadius: "12px", padding: "10px 16px", display: "flex", alignItems: "center", gap: "10px" }}>
            <Sparkles size={16} style={{ color: "var(--rayven-accent)" }} />
            <div>
              <div style={{ fontSize: "10px", fontWeight: "800", color: "var(--rayven-accent)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Automatic Web Scraping Schedule
              </div>
              <div style={{ fontSize: "12px", fontWeight: "700", color: "#ffffff" }}>
                ⚡ ACTIVE — Twice Weekly (Every 3-4 Days)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Scraping & Web Extraction Tester Bar */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(201,168,76,0.1), rgba(18,12,30,0.8))",
          border: "1px solid rgba(201,168,76,0.3)",
          borderRadius: "14px",
          padding: "20px 24px",
          marginBottom: "28px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
          <Sparkles size={18} style={{ color: "var(--rayven-accent)" }} />
          <h2 style={{ fontSize: "15px", fontWeight: "800", color: "#ffffff", margin: 0 }}>
            Live Lead Discovery & Web Extraction Engine Tester
          </h2>
          <span
            style={{
              fontSize: "11px",
              fontWeight: "700",
              color: "var(--rayven-accent)",
              background: "var(--rayven-accent-muted)",
              padding: "2px 10px",
              borderRadius: "20px",
              marginLeft: "auto",
            }}
          >
            Zero-Paid Search & Domain Intelligence
          </span>
        </div>
        <form onSubmit={handleTestScraping} style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <input
            type="text"
            value={scrapingQuery}
            onChange={(e) => setScrapingQuery(e.target.value)}
            placeholder="Enter campaign query (e.g. CEOs, CMOs in Technology & Finance in Nigeria)"
            style={{
              flex: 1,
              minWidth: "280px",
              background: "var(--bg-secondary, #1a1a26)",
              border: "1px solid var(--border, #2a2a3c)",
              borderRadius: "10px",
              padding: "12px 16px",
              color: "#ffffff",
              fontSize: "13px",
              outline: "none",
            }}
          />
          <select
            value={scrapingMaxResults}
            onChange={(e) => setScrapingMaxResults(Number(e.target.value))}
            style={{
              background: "var(--bg-secondary, #1a1a26)",
              border: "1px solid var(--border, #2a2a3c)",
              borderRadius: "10px",
              padding: "12px 14px",
              color: "var(--rayven-accent)",
              fontSize: "13px",
              fontWeight: "700",
              outline: "none",
              cursor: "pointer",
            }}
          >
            <option value={10}>10 Leads</option>
            <option value={25}>25 Leads</option>
            <option value={50}>50 Leads</option>
            <option value={100}>100 Leads</option>
          </select>

          <button
            type="submit"
            disabled={scraping}
            style={{
              background: "var(--rayven-accent)",
              border: "none",
              borderRadius: "10px",
              padding: "12px 24px",
              color: "#ffffff",
              fontSize: "13px",
              fontWeight: "800",
              cursor: scraping ? "not-allowed" : "pointer",
              boxShadow: "0 0 16px var(--rayven-accent-glow)",
              whiteSpace: "nowrap",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Search size={16} />
            {scraping ? "Scraping Web & Enrolling..." : `Extract & Enroll ${scrapingMaxResults} Leads`}
          </button>
        </form>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap", alignItems: "center" }}>
        {[
          { key: "all", label: `All Leads (${leads.length})` },
          { key: "new", label: `New Discovered (${leads.filter((l) => l.status === "new" || l.status === "discovered").length})` },
          { key: "outreach", label: `Outreach Sent (${leads.filter((l) => l.status === "outreach_sent" || l.status === "follow_up").length})` },
          { key: "replied", label: `Replied (${leads.filter((l) => l.status === "replied" || l.reply_count > 0).length})` },
          {
            key: "human",
            label: `🚨 Needs Human Service (${leads.filter((l) => l.needs_human_service).length})`,
            alert: leads.filter((l) => l.needs_human_service).length > 0,
          },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveFilter(tab.key)}
            style={{
              padding: "10px 18px",
              borderRadius: "10px",
              border: tab.alert
                ? "1px solid rgba(239,68,68,0.5)"
                : activeFilter === tab.key
                ? "1px solid #c9a84c"
                : "1px solid var(--border, #2a2a3c)",
              background: tab.alert
                ? "rgba(239,68,68,0.15)"
                : activeFilter === tab.key
                ? "rgba(201,168,76,0.15)"
                : "var(--bg-card, #12121c)",
              color: tab.alert ? "#f87171" : activeFilter === tab.key ? "#c9a84c" : "var(--text-secondary, #9494a8)",
              fontSize: "12px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}

        <button
          onClick={() => loadLeads(true)}
          style={{
            marginLeft: "auto",
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "8px 16px",
            color: "var(--text-secondary)",
            fontSize: "12px",
            fontWeight: "600",
            cursor: "pointer",
          }}
        >
          ↻ Refresh Leads
        </button>
      </div>

      {/* Lead Table */}
      <div
        style={{
          background: "var(--bg-card, #12121c)",
          border: "1px solid var(--border, #2a2a3c)",
          borderRadius: "14px",
          overflow: "hidden",
        }}
      >
        {loading ? (
          <div style={{ padding: "48px", textAlign: "center", color: "var(--text-muted)" }}>
            Loading extracted lead pipeline...
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border, #2a2a3c)", background: "rgba(0,0,0,0.2)" }}>
                {[
                  "Lead / Executive Name",
                  "Designation / Title",
                  "Company & Domain",
                  "Email Address & Confidence",
                  "Contact / Phone",
                  "Position / Seniority",
                  "Status & Progress",
                  "Actions",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "14px 16px",
                      textAlign: "left",
                      fontSize: "11px",
                      fontWeight: "700",
                      color: "#71718a",
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredLeads.map((lead, i) => {
                const p = lead.prospect || {};
                const st = STATUS_CONFIG[lead.status] || {
                  label: lead.status.replace(/_/g, " "),
                  bg: "rgba(113,113,138,0.15)",
                  color: "#9494a8",
                  border: "rgba(113,113,138,0.3)",
                };

                return (
                  <tr
                    key={lead.id}
                    style={{
                      borderBottom: i < filteredLeads.length - 1 ? "1px solid var(--border, #2a2a3c)" : "none",
                      background: lead.needs_human_service ? "rgba(239,68,68,0.04)" : "transparent",
                    }}
                  >
                    {/* Name & LinkedIn */}
                    <td style={{ padding: "14px 16px" }}>
                      <div style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", marginBottom: "2px" }}>
                        {p.full_name || "Executive Decision Maker"}
                      </div>
                      {p.linkedin_url ? (
                        <a
                          href={p.linkedin_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: "11px", color: "#38bdf8", textDecoration: "none" }}
                        >
                          🔗 LinkedIn Profile
                        </a>
                      ) : (
                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Public Web Discovery</span>
                      )}
                    </td>

                    {/* Designation / Title */}
                    <td style={{ padding: "14px 16px", fontSize: "13px", color: "var(--text-primary)" }}>
                      <strong>{p.title || p.designation || "Executive"}</strong>
                    </td>

                    {/* Company */}
                    <td style={{ padding: "14px 16px" }}>
                      <div style={{ fontSize: "13px", fontWeight: "700", color: "#ffffff" }}>
                        {p.company_name || "Target Enterprise"}
                      </div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                        {p.company_domain || "public-web.ng"}
                      </div>
                    </td>

                    {/* Email & Confidence */}
                    <td style={{ padding: "14px 16px" }}>
                      <div style={{ fontSize: "13px", fontFamily: "monospace", color: "#ffffff", marginBottom: "4px" }}>
                        {p.email || "Unverified Pattern"}
                      </div>
                      <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: "700",
                            padding: "2px 8px",
                            borderRadius: "12px",
                            background:
                              (p.email_confidence || 65) >= 70
                                ? "rgba(16,185,129,0.15)"
                                : "rgba(245,158,11,0.15)",
                            color: (p.email_confidence || 65) >= 70 ? "#34d399" : "#fbbf24",
                            border:
                              (p.email_confidence || 65) >= 70
                                ? "1px solid rgba(16,185,129,0.3)"
                                : "1px solid rgba(245,158,11,0.3)",
                          }}
                        >
                          {(p.email_confidence || 65)}% Confidence
                        </span>
                      </div>
                    </td>

                    {/* Phone / Contact */}
                    <td style={{ padding: "14px 16px", fontSize: "12px", color: "var(--text-secondary)" }}>
                      {p.phone || p.contact || "+234 (0) 800-RAYVEN"}
                    </td>

                    {/* Position / Seniority */}
                    <td style={{ padding: "14px 16px", fontSize: "12px", color: "var(--text-secondary)" }}>
                      {p.position || p.department || "C-Suite / Leadership"}
                    </td>

                    {/* Status & Progress Badge */}
                    <td style={{ padding: "14px 16px" }}>
                      <span
                        style={{
                          display: "inline-block",
                          padding: "4px 12px",
                          borderRadius: "20px",
                          fontSize: "11px",
                          fontWeight: "800",
                          background: st.bg,
                          color: st.color,
                          border: `1px solid ${st.border}`,
                          textTransform: "uppercase",
                          letterSpacing: "0.03em",
                        }}
                      >
                        {st.label}
                      </span>
                    </td>

                    {/* Actions */}
                    <td style={{ padding: "14px 16px" }}>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button
                          onClick={() => setSelectedLead(lead)}
                          style={{
                            background: "var(--bg-secondary, #1a1a26)",
                            border: "1px solid var(--border, #2a2a3c)",
                            borderRadius: "6px",
                            padding: "6px 12px",
                            color: "#ffffff",
                            fontSize: "11px",
                            fontWeight: "600",
                            cursor: "pointer",
                          }}
                        >
                          🔍 View Sent Messages & Research
                        </button>
                        <button
                          onClick={async () => {
                            try {
                              await apiFetch(`/api/v1/leads/${lead.id}`, {
                                method: "PUT",
                                body: JSON.stringify({ status: "outreach_sent" }),
                              });
                              alert(`Outreach initiated for ${p.full_name}`);
                              await loadLeads();
                            } catch (e: any) {
                              alert("Error: " + e.message);
                            }
                          }}
                          style={{
                            background: "rgba(201,168,76,0.15)",
                            border: "1px solid #c9a84c",
                            borderRadius: "6px",
                            padding: "6px 12px",
                            color: "#c9a84c",
                            fontSize: "11px",
                            fontWeight: "700",
                            cursor: "pointer",
                          }}
                        >
                          ⚡ Send Email
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}

              {filteredLeads.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: "48px", textAlign: "center", color: "var(--text-muted)" }}>
                    No leads match selected filter. Run the Live Web Extraction test above to discover new leads!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Lead Details & Sent Messages Modal */}
      {selectedLead && (
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
                <h2 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff", marginBottom: "4px" }}>
                  {selectedLead.prospect?.full_name || "Executive Prospect"}
                </h2>
                <div style={{ fontSize: "12px", color: "var(--accent-gold)", fontWeight: "600" }}>
                  {selectedLead.prospect?.title || "Decision Maker"} · {selectedLead.prospect?.company_name || "Target Enterprise"}
                </div>
              </div>
              <button
                onClick={() => setSelectedLead(null)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "22px", cursor: "pointer" }}
              >
                ×
              </button>
            </div>

            {/* Quick Metadata Chips */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", marginBottom: "24px" }}>
              <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: "10px", padding: "12px" }}>
                <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>Email Address</div>
                <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#ffffff", marginTop: "2px" }}>{selectedLead.prospect?.email || "N/A"}</div>
              </div>

              <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: "10px", padding: "12px" }}>
                <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>Phone / Contact</div>
                <div style={{ fontSize: "12px", color: "#ffffff", marginTop: "2px" }}>{selectedLead.prospect?.phone || "+234 (0) 800-RAYVEN"}</div>
              </div>

              <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: "10px", padding: "12px" }}>
                <div style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>Lead Pipeline Status</div>
                <div style={{ fontSize: "12px", fontWeight: "700", color: "#c9a84c", marginTop: "2px" }}>{selectedLead.status.toUpperCase()}</div>
              </div>
            </div>

            {/* Sent Outreach Messages & AI Personalization Section */}
            <div style={{ background: "rgba(201,168,76,0.06)", border: "1px solid rgba(201,168,76,0.25)", borderRadius: "12px", padding: "20px", marginBottom: "20px" }}>
              <h3 style={{ fontSize: "14px", fontWeight: "800", color: "#c9a84c", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <Send size={16} /> Sent Outreach & AI Personalization Intelligence ({leadMessages.length} Messages)
              </h3>

              {loadingMessages ? (
                <div style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                  Fetching sent outreach records...
                </div>
              ) : leadMessages.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                  {leadMessages.map((msg: any) => (
                    <div key={msg.id} style={{ background: "var(--bg-secondary, #12121c)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                        <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--rayven-accent)", textTransform: "uppercase" }}>
                          {msg.direction.toUpperCase()} ({msg.status.toUpperCase()})
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                          {msg.sent_at ? new Date(msg.sent_at).toLocaleString() : "Recently Dispatched"}
                        </div>
                      </div>

                      <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                        Subject Line:
                      </div>
                      <div style={{ fontSize: "13px", fontWeight: "700", color: "#ffffff", marginBottom: "10px" }}>
                        {msg.subject}
                      </div>

                      <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                        Outreach Email Body:
                      </div>
                      <div style={{ fontSize: "13px", color: "#e2e8f0", lineHeight: "1.6", whiteSpace: "pre-wrap", background: "rgba(0,0,0,0.25)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                        {msg.body}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ background: "var(--bg-secondary, #12121c)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
                  <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                    Status: Draft Pending Dispatch
                  </div>
                  <div style={{ fontSize: "13px", color: "#e2e8f0", lineHeight: "1.6", whiteSpace: "pre-wrap", background: "rgba(0,0,0,0.2)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                    {`Dear ${selectedLead.prospect?.first_name || "Executive"},\n\nAt Rayven Strategic Communications, we help leaders engineer narrative architecture and strategic PR to turn brand perception into high-trust client relationships.\n\nWould you be open to a brief strategic exchange this week?\n\nWarm regards,\nRayven Strategic Communications Team`}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                onClick={() => setSelectedLead(null)}
                style={{ background: "transparent", border: "1px solid var(--border)", color: "#94a3b8", borderRadius: "8px", padding: "10px 18px", fontSize: "13px", cursor: "pointer" }}
              >
                Close
              </button>
              <a
                href="/dashboard/conversations"
                style={{
                  background: "linear-gradient(135deg, #c9a84c, #a87830)",
                  color: "#0a0a0f",
                  borderRadius: "8px",
                  padding: "10px 20px",
                  fontSize: "13px",
                  fontWeight: "800",
                  textDecoration: "none",
                  display: "inline-block",
                }}
              >
                Open Inbox & Thread →
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
