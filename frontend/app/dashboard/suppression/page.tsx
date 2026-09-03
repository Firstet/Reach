"use client";

import { useEffect, useState } from "react";

interface SuppressionItem {
  id: string;
  suppression_type: string;
  value: string;
  reason: string | null;
  created_at: string;
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

export default function SuppressionPage() {
  const [items, setItems] = useState<SuppressionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ suppression_type: "domain", value: "", reason: "" });

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/suppression");
      setItems(data.items);
    } catch {
      /* not connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/api/v1/suppression", { method: "POST", body: JSON.stringify(form) });
      setShowAdd(false);
      setForm({ suppression_type: "domain", value: "", reason: "" });
      load();
    } catch (e) {
      alert("Failed to add suppression: " + e);
    }
  };

  const handleRemove = async (id: string) => {
    if (!confirm("Remove from blocklist?")) return;
    try {
      await apiFetch(`/api/v1/suppression/${id}`, { method: "DELETE" });
      load();
    } catch (e) {
      alert("Failed to remove: " + e);
    }
  };

  return (
    <div style={{ padding: "32px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "20px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px" }}>
            Suppression & Blocklist
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Suppressed emails and domains are strictly excluded from all outbound activity
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "10px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}
        >
          + Add Blocklist Entry
        </button>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading blocklist...
        </div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: "center", padding: "64px 24px", background: "var(--bg-card)", border: "1px dashed var(--border)", borderRadius: "12px" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🛡️</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>Blocklist is empty</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            No emails or domains are currently suppressed.
          </p>
        </div>
      ) : (
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "12px", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-secondary)" }}>
                {["Type", "Value / Domain / Email", "Reason", "Added Date", "Action"].map(h => (
                  <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={item.id} style={{ borderBottom: i < items.length - 1 ? "1px solid var(--border-subtle)" : "none" }}>
                  <td style={{ padding: "12px 16px" }}>
                    <span style={{ padding: "2px 8px", borderRadius: "20px", fontSize: "10px", fontWeight: "700", textTransform: "uppercase", background: item.suppression_type === "domain" ? "rgba(201,168,76,0.15)" : "rgba(76,123,201,0.15)", color: item.suppression_type === "domain" ? "#c9a84c" : "#4c7bc9" }}>
                      {item.suppression_type}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px", fontSize: "13px", fontWeight: "600", color: "var(--text-primary)" }}>{item.value}</td>
                  <td style={{ padding: "12px 16px", fontSize: "12px", color: "var(--text-secondary)" }}>{item.reason || "—"}</td>
                  <td style={{ padding: "12px 16px", fontSize: "11px", color: "var(--text-muted)" }}>{new Date(item.created_at).toLocaleDateString()}</td>
                  <td style={{ padding: "12px 16px" }}>
                    <button onClick={() => handleRemove(item.id)} style={{ background: "transparent", border: "1px solid var(--border)", color: "#c94c4c", borderRadius: "6px", padding: "4px 10px", fontSize: "11px", cursor: "pointer" }}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAdd && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "24px" }}>
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "16px", padding: "28px", width: "100%", maxWidth: "480px", margin: "auto" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "20px" }}>Add to Blocklist</h2>
            <form onSubmit={handleAdd}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Type</label>
                <select value={form.suppression_type} onChange={(e) => setForm(f => ({ ...f, suppression_type: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }}>
                  <option value="domain">Domain (e.g. competitor.com)</option>
                  <option value="email">Specific Email (e.g. john@domain.com)</option>
                </select>
              </div>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Domain or Email Value</label>
                <input required placeholder="e.g. company.com or person@email.com" value={form.value} onChange={(e) => setForm(f => ({ ...f, value: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }} />
              </div>
              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Reason</label>
                <input placeholder="e.g. Competitor, Unsubscribed, Opt-out" value={form.reason} onChange={(e) => setForm(f => ({ ...f, reason: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }} />
              </div>
              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button type="button" onClick={() => setShowAdd(false)} style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)", borderRadius: "8px", padding: "9px 16px", fontSize: "13px", cursor: "pointer" }}>Cancel</button>
                <button type="submit" style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}>Add Entry</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
