"use client";

import { useEffect, useState } from "react";

interface ApprovalItem {
  id: string;
  lead_id: string;
  subject: string;
  body: string;
  status: string;
  created_at: string;
  prospect: { full_name: string; title: string; email: string };
  company_name: string;
  campaign_name: string;
  score: number | null;
  why_rayven: string | null;
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

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingItem, setEditingItem] = useState<ApprovalItem | null>(null);
  const [editSubject, setEditSubject] = useState("");
  const [editBody, setEditBody] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/outreach/approvals?status_filter=pending");
      setApprovals(data.items);
    } catch {
      /* not connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleApprove = async (id: string, subject?: string, body?: string) => {
    try {
      await apiFetch(`/api/v1/outreach/approvals/${id}/approve`, {
        method: "POST",
        body: JSON.stringify({ subject, body }),
      });
      setEditingItem(null);
      load();
    } catch (e) {
      alert("Approval failed: " + e);
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt("Enter rejection reason:");
    if (!reason) return;
    try {
      await apiFetch(`/api/v1/outreach/approvals/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ rejection_reason: reason }),
      });
      load();
    } catch (e) {
      alert("Rejection failed: " + e);
    }
  };

  return (
    <div style={{ padding: "32px" }}>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "20px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px" }}>
          Outreach Approval Queue
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          {approvals.length} AI-generated draft emails awaiting human review before sending
        </p>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading approval queue...
        </div>
      ) : approvals.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "var(--bg-card)",
            border: "1px dashed var(--border)",
            borderRadius: "12px",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>✓</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>All clear!</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            No drafts currently require manual review.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {approvals.map((item) => (
            <div
              key={item.id}
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "12px",
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
              }}
            >
              {/* Header bar */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "12px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                    <h3 style={{ fontSize: "16px", fontWeight: "700" }}>{item.prospect.full_name}</h3>
                    <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                      {item.prospect.title} @ <strong>{item.company_name}</strong>
                    </span>
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    Campaign: {item.campaign_name} · Email: {item.prospect.email}
                  </div>
                </div>
                {item.score != null && (
                  <div
                    style={{
                      background: "rgba(76,184,156,0.15)",
                      color: "#4cb89c",
                      padding: "4px 10px",
                      borderRadius: "20px",
                      fontSize: "12px",
                      fontWeight: "700",
                    }}
                  >
                    Score: {Math.round(item.score)}pt
                  </div>
                )}
              </div>

              {/* Research insight context */}
              {item.why_rayven && (
                <div
                  style={{
                    background: "rgba(201,168,76,0.08)",
                    border: "1px solid rgba(201,168,76,0.2)",
                    borderRadius: "8px",
                    padding: "10px 14px",
                    fontSize: "12px",
                    color: "var(--accent-gold)",
                  }}
                >
                  💡 <strong>Strategic Match Hook:</strong> {item.why_rayven}
                </div>
              )}

              {/* Draft preview */}
              <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "16px" }}>
                <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-primary)", marginBottom: "8px" }}>
                  Subject: {item.subject}
                </div>
                <div style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", whiteSpace: "pre-wrap" }}>
                  {item.body}
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button
                  onClick={() => handleReject(item.id)}
                  style={{
                    background: "rgba(201,76,76,0.1)",
                    border: "1px solid rgba(201,76,76,0.3)",
                    color: "#c94c4c",
                    borderRadius: "8px",
                    padding: "8px 16px",
                    fontSize: "13px",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  Reject
                </button>
                <button
                  onClick={() => {
                    setEditingItem(item);
                    setEditSubject(item.subject);
                    setEditBody(item.body);
                  }}
                  style={{
                    background: "var(--bg-hover)",
                    border: "1px solid var(--border)",
                    color: "var(--text-primary)",
                    borderRadius: "8px",
                    padding: "8px 16px",
                    fontSize: "13px",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  Edit Draft
                </button>
                <button
                  onClick={() => handleApprove(item.id)}
                  style={{
                    background: "linear-gradient(135deg, #c9a84c, #a87830)",
                    color: "#0a0a0f",
                    border: "none",
                    borderRadius: "8px",
                    padding: "8px 20px",
                    fontSize: "13px",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  Approve & Send
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      {editingItem && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.75)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "24px",
          }}
        >
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "16px",
              padding: "28px",
              width: "100%",
              maxWidth: "600px",
            }}
          >
            <h2 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "20px" }}>Edit Outreach Draft</h2>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Subject Line</label>
              <input
                value={editSubject}
                onChange={(e) => setEditSubject(e.target.value)}
                style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }}
              />
            </div>

            <div style={{ marginBottom: "24px" }}>
              <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Email Body</label>
              <textarea
                value={editBody}
                onChange={(e) => setEditBody(e.target.value)}
                rows={8}
                style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px", resize: "vertical" }}
              />
            </div>

            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                onClick={() => setEditingItem(null)}
                style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)", borderRadius: "8px", padding: "9px 16px", fontSize: "13px", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleApprove(editingItem.id, editSubject, editBody)}
                style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}
              >
                Save & Approve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
