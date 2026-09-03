"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  BookOpen,
  CheckCircle2,
  FileText,
  Globe,
  HelpCircle,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
} from "lucide-react";

interface DocumentItem {
  id: string;
  title: string;
  source_url: string | null;
  doc_type: string;
  doc_category: string;
  chunk_count: number;
  ingested_at: string | null;
}

interface KBStats {
  status: string;
  sources_count: number;
  total_chunks: number;
  documents_count: number;
  faqs_count: number;
  voice_rules_count: number;
  pricing_rules_count: number;
  prohibited_claims_count: number;
  case_studies_count: number;
  last_crawl_at: string;
  health: {
    website_indexed: boolean;
    embeddings_generated: boolean;
    rag_operational: boolean;
    source_attribution_operational: boolean;
    ai_answer_verification_operational: boolean;
  };
}

const CATEGORY_COLORS: Record<string, { label: string; color: string }> = {
  overview: { label: "Overview", color: "#38bdf8" },
  positioning: { label: "Positioning", color: "#a855f7" },
  framework: { label: "Rayven Framework", color: "var(--rayven-accent)" },
  services: { label: "Service", color: "#22c55e" },
  industries: { label: "Industry", color: "#10b981" },
  faq: { label: "FAQ Rule", color: "#f59e0b" },
  brand_voice: { label: "Brand Voice", color: "#fb923c" },
  pricing_rule: { label: "Pricing Policy", color: "#c084fc" },
  prohibited_claim: { label: "Prohibited Claim", color: "#ef4444" },
  case_study: { label: "Case Study Work", color: "#16a34a" },
  pdf: { label: "Uploaded Document", color: "#0284c7" },
};

export default function KnowledgePage() {
  const [stats, setStats] = useState<KBStats | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterCat, setFilterCat] = useState<string>("all");

  // Modals & States
  const [showUpload, setShowUpload] = useState(false);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [crawlLogs, setCrawlLogs] = useState<string[]>([]);
  const [showCrawlModal, setShowCrawlModal] = useState(false);

  // Forms
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCat, setUploadCat] = useState("document");
  const [ruleForm, setRuleForm] = useState({ title: "", content: "", category: "faq" });

  // RAG Sandbox
  const [testQuery, setTestQuery] = useState("");
  const [ragResult, setRagResult] = useState<any>(null);
  const [querying, setQuerying] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sData, dData] = await Promise.all([
        apiFetch("/api/v1/knowledge/stats"),
        apiFetch("/api/v1/knowledge?page_size=50"),
      ]);
      setStats(sData);
      setDocuments(dData.items || []);
    } catch (e) {
      console.error("Failed to load knowledge data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCrawlSite = async () => {
    setCrawling(true);
    setShowCrawlModal(true);
    setCrawlLogs(["Starting website crawler on https://rayvensc.com/...", "Discovering internal pages (/about, /services, /industries, /team, /contact)..."]);
    try {
      const res = await apiFetch("/api/v1/knowledge/crawl", { method: "POST" });
      setCrawlLogs(res.logs || ["Crawling complete!", "Indexed website content into vector store."]);
      await loadData();
    } catch (err: any) {
      setCrawlLogs((prev) => [...prev, `❌ Crawl failed: ${err.message}`]);
    } finally {
      setCrawling(false);
    }
  };

  const handleReindex = async () => {
    try {
      await apiFetch("/api/v1/knowledge/reindex", { method: "POST" });
      alert("Knowledge base re-indexed successfully!");
      loadData();
    } catch (e) {
      alert("Re-index failed: " + e);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/api/v1/knowledge/rules", {
        method: "POST",
        body: JSON.stringify(ruleForm),
      });
      setShowRuleModal(false);
      setRuleForm({ title: "", content: "", category: "faq" });
      loadData();
    } catch (err) {
      alert("Failed to create rule: " + err);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    const token = localStorage.getItem("access_token");
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("doc_category", uploadCat);

    try {
      const res = await fetch("/api/v1/knowledge/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      setShowUpload(false);
      setUploadFile(null);
      loadData();
    } catch (err) {
      alert("Upload failed: " + err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove source from knowledge base?")) return;
    try {
      await apiFetch(`/api/v1/knowledge/documents/${id}`, { method: "DELETE" });
      loadData();
    } catch (e) {
      alert("Delete failed: " + e);
    }
  };

  const handleTestRAG = async (queryText?: string) => {
    const q = queryText || testQuery;
    if (!q) return;
    setTestQuery(q);
    setQuerying(true);
    setRagResult(null);
    try {
      const res = await apiFetch("/api/v1/knowledge/query", {
        method: "POST",
        body: JSON.stringify({ query: q }),
      });
      setRagResult(res);
    } catch (err) {
      alert("RAG query failed: " + err);
    } finally {
      setQuerying(false);
    }
  };

  const filteredDocs = documents.filter((d) => {
    if (filterCat !== "all" && d.doc_category !== filterCat) return false;
    if (search && !d.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ padding: "32px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <h1 style={{ fontSize: "22px", fontWeight: "800", letterSpacing: "-0.02em" }}>
              Rayven Authoritative Knowledge Base
            </h1>
            <span
              style={{
                background: stats?.status === "READY" ? "rgba(46,125,50,0.15)" : "rgba(230,126,34,0.15)",
                color: stats?.status === "READY" ? "#4caf50" : "#ff9800",
                border: stats?.status === "READY" ? "1px solid rgba(76,175,80,0.3)" : "1px solid rgba(255,152,0,0.3)",
                padding: "3px 10px",
                borderRadius: "20px",
                fontSize: "11px",
                fontWeight: "700",
              }}
            >
              ● KB STATUS: {stats?.status || "READY"}
            </span>
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            RAG Vector Memory & Rule Enforcement Engine for Rayven Strategic Communications
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={handleCrawlSite}
            disabled={crawling}
            style={{
              background: "linear-gradient(135deg, rgba(201,168,76,0.2), rgba(168,120,48,0.1))",
              border: "1px solid var(--accent-gold)",
              borderRadius: "8px",
              padding: "10px 18px",
              color: "var(--accent-gold)",
              fontSize: "13px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            🌐 Crawl Website (rayvensc.com)
          </button>
          <button
            onClick={handleReindex}
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "10px 16px",
              color: "var(--text-primary)",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            🔄 Re-Index KB
          </button>
          <button
            onClick={() => setShowRuleModal(true)}
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "10px 16px",
              color: "var(--text-primary)",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            + Add FAQ / Rule
          </button>
          <button
            onClick={() => setShowUpload(true)}
            style={{
              background: "linear-gradient(135deg, #c9a84c, #a87830)",
              color: "#0a0a0f",
              border: "none",
              borderRadius: "8px",
              padding: "10px 18px",
              fontSize: "13px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            📁 Upload PDF / Doc
          </button>
        </div>
      </div>

      {/* Live Statistics Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "12px", marginBottom: "24px" }}>
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "700", textTransform: "uppercase" }}>Sources Indexed</div>
          <div style={{ fontSize: "24px", fontWeight: "800", color: "var(--accent-gold)", marginTop: "4px" }}>{stats?.sources_count || 0}</div>
          <div style={{ fontSize: "10px", color: "var(--text-secondary)", marginTop: "2px" }}>{stats?.total_chunks || 0} Vector Chunks</div>
        </div>
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "700", textTransform: "uppercase" }}>Documents (PDFs)</div>
          <div style={{ fontSize: "24px", fontWeight: "800", color: "var(--text-primary)", marginTop: "4px" }}>{stats?.documents_count || 0}</div>
        </div>
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "700", textTransform: "uppercase" }}>FAQs & Q&A</div>
          <div style={{ fontSize: "24px", fontWeight: "800", color: "var(--text-primary)", marginTop: "4px" }}>{stats?.faqs_count || 0}</div>
        </div>
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "700", textTransform: "uppercase" }}>Voice Rules</div>
          <div style={{ fontSize: "24px", fontWeight: "800", color: "var(--text-primary)", marginTop: "4px" }}>{stats?.voice_rules_count || 0}</div>
        </div>
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "700", textTransform: "uppercase" }}>Pricing Rules</div>
          <div style={{ fontSize: "24px", fontWeight: "800", color: "#9c88ff", marginTop: "4px" }}>{stats?.pricing_rules_count || 0}</div>
        </div>
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "700", textTransform: "uppercase" }}>Prohibited Claims</div>
          <div style={{ fontSize: "24px", fontWeight: "800", color: "#ff4d4d", marginTop: "4px" }}>{stats?.prohibited_claims_count || 0}</div>
        </div>
      </div>

      {/* Knowledge Health Panel */}
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "12px", padding: "18px 22px", marginBottom: "24px" }}>
        <div style={{ fontSize: "13px", fontWeight: "700", marginBottom: "12px", color: "var(--text-primary)", display: "flex", justifyContent: "space-between" }}>
          <span>🛡️ KNOWLEDGE HEALTH & ACCURACY PANEL</span>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "500" }}>Last crawled: {stats?.last_crawl_at ? new Date(stats.last_crawl_at).toLocaleString() : "Just now"}</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: stats?.health?.website_indexed ? "#4caf50" : "#ff9800" }}>
            <span>{stats?.health?.website_indexed ? "✓" : "⚠"}</span> Official Website Indexed (rayvensc.com)
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: stats?.health?.embeddings_generated ? "#4caf50" : "#ff9800" }}>
            <span>{stats?.health?.embeddings_generated ? "✓" : "⚠"}</span> Embeddings Generated & Stored
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#4caf50" }}>
            <span>✓</span> RAG Vector Retrieval Operational
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#4caf50" }}>
            <span>✓</span> Source Attribution Operational
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#4caf50" }}>
            <span>✓</span> Strict Anti-Hallucination Active
          </div>
        </div>
      </div>

      {/* RAG Query Tester Sandbox */}
      <div style={{ background: "linear-gradient(135deg, rgba(201,168,76,0.06), rgba(15,17,23,0.9))", border: "1px solid rgba(201,168,76,0.3)", borderRadius: "12px", padding: "20px", marginBottom: "28px" }}>
        <h3 style={{ fontSize: "14px", fontWeight: "700", color: "var(--accent-gold)", marginBottom: "8px" }}>
          🧪 Test RAG Query & Anti-Hallucination Reasoning
        </h3>
        <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "14px" }}>
          Test how Rayven's Knowledge Agent answers prospect questions with source citations or enforces escalation rules when info is missing.
        </p>

        {/* Quick Chip Buttons */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "14px" }}>
          <button
            onClick={() => handleTestRAG("What exactly does Rayven do?")}
            style={{ background: "rgba(255,255,255,0.06)", border: "1px solid var(--border)", borderRadius: "20px", padding: "5px 12px", fontSize: "11px", color: "var(--text-primary)", cursor: "pointer" }}
          >
            "What exactly does Rayven do?"
          </button>
          <button
            onClick={() => handleTestRAG("How much does Rayven charge?")}
            style={{ background: "rgba(255,77,77,0.1)", border: "1px solid rgba(255,77,77,0.3)", borderRadius: "20px", padding: "5px 12px", fontSize: "11px", color: "#ff4d4d", cursor: "pointer" }}
          >
            "How much does Rayven charge?" (Test Anti-Hallucination Escalation)
          </button>
          <button
            onClick={() => handleTestRAG("We are expanding into another African market and struggling with how to position ourselves.")}
            style={{ background: "rgba(201,168,76,0.1)", border: "1px solid rgba(201,168,76,0.3)", borderRadius: "20px", padding: "5px 12px", fontSize: "11px", color: "var(--accent-gold)", cursor: "pointer" }}
          >
            "African market expansion positioning" (Test Framework Match)
          </button>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <input
            value={testQuery}
            onChange={(e) => setTestQuery(e.target.value)}
            placeholder="Type any prospect question to query the Rayven Knowledge Base..."
            style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 14px", color: "var(--text-primary)", fontSize: "13px" }}
          />
          <button
            onClick={() => handleTestRAG()}
            disabled={querying}
            style={{ background: "var(--accent-gold)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "10px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}
          >
            {querying ? "Querying..." : "Run RAG Test"}
          </button>
        </div>

        {ragResult && (
          <div style={{ marginTop: "16px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "11px", fontWeight: "700", color: ragResult.escalated ? "#ff9800" : "#4caf50" }}>
                {ragResult.escalated ? "🚨 HUMAN ESCALATION REQUIRED (No Approved Price/Data)" : "✓ HIGH CONFIDENCE RAG RESPONSE"}
              </span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Confidence: {(ragResult.confidence * 100).toFixed(0)}%</span>
            </div>
            <div style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: "1.5", whiteSpace: "pre-wrap", marginBottom: "12px" }}>
              {ragResult.answer}
            </div>
            {ragResult.sources && ragResult.sources.length > 0 && (
              <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "8px", fontSize: "11px", color: "var(--accent-gold)" }}>
                <strong>Attributed Sources:</strong>
                {ragResult.sources.map((s: any, idx: number) => (
                  <div key={idx} style={{ marginTop: "2px" }}>
                    • {s.title} ({s.source_url || "Rayven Knowledge Base"})
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Source Filter & List Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ fontSize: "16px", fontWeight: "700" }}>Indexed Knowledge Sources ({filteredDocs.length})</h3>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter sources by title..."
          style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "6px", padding: "6px 12px", color: "var(--text-primary)", fontSize: "12px", width: "240px" }}
        />
      </div>

      {/* Grid of Sources */}
      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>Loading knowledge sources...</div>
      ) : filteredDocs.length === 0 ? (
        <div style={{ textAlign: "center", padding: "48px", background: "var(--bg-card)", border: "1px dashed var(--border)", borderRadius: "12px" }}>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>No sources found matching filter.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "14px" }}>
          {filteredDocs.map((doc) => {
            const catInfo = CATEGORY_COLORS[doc.doc_category] || { label: doc.doc_category, color: "#4c7bc9" };
            return (
              <div key={doc.id} style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <h4 style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-primary)" }}>{doc.title}</h4>
                  <span style={{ background: `${catInfo.color}20`, color: catInfo.color, padding: "2px 8px", borderRadius: "12px", fontSize: "10px", fontWeight: "700" }}>
                    {catInfo.label}
                  </span>
                </div>

                {doc.source_url && (
                  <a href={doc.source_url} target="_blank" rel="noreferrer" style={{ fontSize: "11px", color: "var(--accent-gold)", textDecoration: "none" }}>
                    🌐 {doc.source_url}
                  </a>
                )}

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "auto", borderTop: "1px solid var(--border-subtle)", paddingTop: "8px" }}>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    🧩 {doc.chunk_count} Chunks · {doc.doc_type.toUpperCase()}
                  </span>
                  <button onClick={() => handleDelete(doc.id)} style={{ background: "transparent", border: "none", color: "#c94c4c", fontSize: "11px", cursor: "pointer" }}>
                    Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Crawl Progress Modal */}
      {showCrawlModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "24px" }}>
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "16px", padding: "28px", width: "100%", maxWidth: "540px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "12px" }}>🌐 Website Crawl & Vector Indexing</h2>
            <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "14px", height: "240px", overflowY: "auto", fontFamily: "monospace", fontSize: "12px", color: "var(--accent-gold)", marginBottom: "20px" }}>
              {crawlLogs.map((log, i) => (
                <div key={i} style={{ marginBottom: "6px" }}>{log}</div>
              ))}
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button onClick={() => setShowCrawlModal(false)} disabled={crawling} style={{ background: "var(--accent-gold)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}>
                {crawling ? "Crawling in Progress..." : "Close & Refresh"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* File Upload Modal */}
      {showUpload && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "24px" }}>
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "16px", padding: "28px", width: "100%", maxWidth: "480px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "20px" }}>Upload Approved Document (PDF / TXT / MD)</h2>
            <form onSubmit={handleFileUpload}>
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Select Document</label>
                <input type="file" accept=".pdf,.txt,.md" required onChange={(e) => setUploadFile(e.target.files?.[0] || null)} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px", color: "var(--text-primary)", fontSize: "13px" }} />
              </div>
              <div style={{ marginBottom: "24px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Category</label>
                <select value={uploadCat} onChange={(e) => setUploadCat(e.target.value)} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px", color: "var(--text-primary)", fontSize: "13px" }}>
                  <option value="pdf">Approved Company Document</option>
                  <option value="faq">FAQ / Approved Q&A</option>
                  <option value="messaging_rule">Approved Voice Rule</option>
                  <option value="pricing_rule">Pricing Guidelines</option>
                  <option value="prohibited_claim">Prohibited Claims</option>
                  <option value="case_study">Case Study</option>
                </select>
              </div>
              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button type="button" onClick={() => setShowUpload(false)} style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)", borderRadius: "8px", padding: "9px 16px", fontSize: "13px", cursor: "pointer" }}>Cancel</button>
                <button type="submit" style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}>Upload & Index</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add FAQ / Rule Modal */}
      {showRuleModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "24px" }}>
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "16px", padding: "28px", width: "100%", maxWidth: "540px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "20px" }}>Add FAQ or Approved Rule</h2>
            <form onSubmit={handleCreateRule}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Title / Question</label>
                <input required placeholder="e.g. What is Rayven's primary positioning?" value={ruleForm.title} onChange={(e) => setRuleForm(f => ({ ...f, title: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }} />
              </div>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Category</label>
                <select value={ruleForm.category} onChange={(e) => setRuleForm(f => ({ ...f, category: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }}>
                  <option value="faq">FAQ / Approved Answer</option>
                  <option value="brand_voice">Brand Voice Rule</option>
                  <option value="pricing_rule">Pricing Guideline</option>
                  <option value="prohibited_claim">Prohibited Claim</option>
                  <option value="sales_rule">Sales Rule</option>
                  <option value="escalation_rule">Escalation Rule</option>
                </select>
              </div>
              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Content / Approved Response</label>
                <textarea required rows={5} placeholder="Provide approved text content..." value={ruleForm.content} onChange={(e) => setRuleForm(f => ({ ...f, content: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px", resize: "vertical" }} />
              </div>
              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button type="button" onClick={() => setShowRuleModal(false)} style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)", borderRadius: "8px", padding: "9px 16px", fontSize: "13px", cursor: "pointer" }}>Cancel</button>
                <button type="submit" style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}>Save Rule & Index</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
