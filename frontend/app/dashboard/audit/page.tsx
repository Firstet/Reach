"use client";

import { useEffect, useState } from "react";

interface AuditEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: any;
  ip_address: string | null;
  created_at: string;
}

const ACTION_COLORS: Record<string, string> = {
  user_login: "#4c7bc9",
  campaign_created: "#c9a84c",
  campaign_started: "#4cb89c",
  campaign_paused: "#c9a84c",
  lead_created: "#4c7bc9",
  lead_escalated: "#c94c4c",
  conversation_escalated: "#c94c4c",
  human_replied: "#9c4cc9",
  config_updated: "#9090a8",
  knowledge_ingested: "#4caf50",
  message_sent: "#4c7bc9",
};

async function apiFetch(path: string) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(path, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const load = async (p = 1) => {
    setLoading(true);
    try {
      const data = await apiFetch(`/api/v1/audit?page=${p}&page_size=50`);
      setLogs(data.items);
      setTotal(data.total);
    } catch {
      /* not connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(page); }, [page]);

  return (
    <div style={{ padding: "32px" }}>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "20px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px" }}>
          Audit Log
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          {total} immutable audit events · Every agent and human action is recorded
        </p>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading audit log...
        </div>
      ) : logs.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "var(--bg-card)",
            border: "1px dashed var(--border)",
            borderRadius: "12px",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>◳</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>No audit events yet</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            Events will appear here as you and the agent take actions.
          </p>
        </div>
      ) : (
        <>
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              overflow: "hidden",
              marginBottom: "16px",
            }}
          >
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-secondary)" }}>
                  {["Time", "Action", "Resource", "Details", "IP"].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "10px 16px",
                        textAlign: "left",
                        fontSize: "10px",
                        fontWeight: "700",
                        color: "var(--text-muted)",
                        letterSpacing: "0.08em",
                        textTransform: "uppercase",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {logs.map((log, i) => {
                  const actionColor = ACTION_COLORS[log.action] || "#9090a8";
                  return (
                    <tr
                      key={log.id}
                      style={{
                        borderBottom: i < logs.length - 1 ? "1px solid var(--border-subtle)" : "none",
                      }}
                    >
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: "11px",
                          color: "var(--text-muted)",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 16px" }}>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: "700",
                            color: actionColor,
                            background: actionColor + "18",
                            padding: "2px 8px",
                            borderRadius: "20px",
                            letterSpacing: "0.03em",
                          }}
                        >
                          {log.action}
                        </span>
                      </td>
                      <td style={{ padding: "10px 16px", fontSize: "12px", color: "var(--text-secondary)" }}>
                        {log.resource_type}
                        {log.resource_id && (
                          <span style={{ color: "var(--text-muted)", fontSize: "10px", display: "block" }}>
                            {log.resource_id.slice(0, 8)}...
                          </span>
                        )}
                      </td>
                      <td
                        style={{
                          padding: "10px 16px",
                          fontSize: "11px",
                          color: "var(--text-muted)",
                          maxWidth: "200px",
                        }}
                      >
                        {log.details ? JSON.stringify(log.details).slice(0, 60) : "—"}
                      </td>
                      <td style={{ padding: "10px 16px", fontSize: "11px", color: "var(--text-muted)" }}>
                        {log.ip_address || "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div style={{ display: "flex", justifyContent: "center", gap: "8px" }}>
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "7px",
                padding: "7px 14px",
                color: page <= 1 ? "var(--text-muted)" : "var(--text-secondary)",
                fontSize: "12px",
                cursor: page <= 1 ? "not-allowed" : "pointer",
              }}
            >
              ← Previous
            </button>
            <span
              style={{
                padding: "7px 14px",
                fontSize: "12px",
                color: "var(--text-secondary)",
              }}
            >
              Page {page}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * 50 >= total}
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "7px",
                padding: "7px 14px",
                color: page * 50 >= total ? "var(--text-muted)" : "var(--text-secondary)",
                fontSize: "12px",
                cursor: page * 50 >= total ? "not-allowed" : "pointer",
              }}
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
