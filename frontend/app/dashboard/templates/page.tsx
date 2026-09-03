"use client";

import { useEffect, useState } from "react";

interface Template {
  id: string;
  name: string;
  category: string;
  subject_template: string;
  body_template: string;
  variables: string[];
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

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", category: "outreach", subject_template: "", body_template: "" });

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/templates");
      setTemplates(data.items);
    } catch {
      /* not connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/api/v1/templates", { method: "POST", body: JSON.stringify(form) });
      setShowCreate(false);
      setForm({ name: "", category: "outreach", subject_template: "", body_template: "" });
      load();
    } catch (e) {
      alert("Failed to create template: " + e);
    }
  };

  return (
    <div style={{ padding: "32px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "20px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px" }}>
            Email Templates Library
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Reusable outreach frameworks and messaging patterns
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "10px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}
        >
          + New Template
        </button>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading templates...
        </div>
      ) : templates.length === 0 ? (
        <div style={{ textAlign: "center", padding: "64px 24px", background: "var(--bg-card)", border: "1px dashed var(--border)", borderRadius: "12px" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>📑</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>No custom templates</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            Add reusable email templates to guide the AI writer agent.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "16px" }}>
          {templates.map((t) => (
            <div key={t.id} style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "12px", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                <h3 style={{ fontSize: "15px", fontWeight: "700" }}>{t.name}</h3>
                <span style={{ background: "rgba(201,168,76,0.15)", color: "#c9a84c", padding: "2px 8px", borderRadius: "20px", fontSize: "10px", fontWeight: "700", textTransform: "uppercase" }}>{t.category}</span>
              </div>
              <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-primary)", marginBottom: "6px" }}>
                Subj: {t.subject_template}
              </div>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4", whiteSpace: "pre-wrap" }}>
                {t.body_template.slice(0, 150)}...
              </p>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: "24px" }}>
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "16px", padding: "28px", width: "100%", maxWidth: "540px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "20px" }}>New Template</h2>
            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Template Name</label>
                <input required value={form.name} onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }} />
              </div>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Subject Template</label>
                <input required value={form.subject_template} onChange={(e) => setForm(f => ({ ...f, subject_template: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px" }} />
              </div>
              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Body Template</label>
                <textarea required rows={6} value={form.body_template} onChange={(e) => setForm(f => ({ ...f, body_template: e.target.value }))} style={{ width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px", resize: "vertical" }} />
              </div>
              <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                <button type="button" onClick={() => setShowCreate(false)} style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)", borderRadius: "8px", padding: "9px 16px", fontSize: "13px", cursor: "pointer" }}>Cancel</button>
                <button type="submit" style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "700", cursor: "pointer" }}>Create Template</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
