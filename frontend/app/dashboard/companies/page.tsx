"use client";

import { useEffect, useState } from "react";

interface Company {
  id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  size: string | null;
  country: string | null;
  description: string | null;
  research_summary: string | null;
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

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const q = search ? `?search=${encodeURIComponent(search)}` : "?page_size=50";
      const data = await apiFetch(`/api/v1/companies${q}`);
      setCompanies(data.items);
      setTotal(data.total);
    } catch {
      /* not connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load();
  };

  return (
    <div style={{ padding: "32px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
        <div>
          <h1 style={{ fontSize: "20px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px" }}>
            Companies Directory
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            {total} target companies discovered and researched
          </p>
        </div>
        <form onSubmit={handleSearch} style={{ display: "flex", gap: "8px" }}>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search companies..."
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "8px 14px",
              color: "var(--text-primary)",
              fontSize: "13px",
              outline: "none",
            }}
          />
          <button
            type="submit"
            style={{
              background: "var(--bg-hover)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "8px 16px",
              color: "var(--text-primary)",
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            Search
          </button>
        </form>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading companies...
        </div>
      ) : companies.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "var(--bg-card)",
            border: "1px dashed var(--border)",
            borderRadius: "12px",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🏢</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>No companies found</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            Trigger a discovery run to populate target companies.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "16px" }}>
          {companies.map((c) => (
            <div
              key={c.id}
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "12px",
                padding: "20px",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <h3 style={{ fontSize: "16px", fontWeight: "700", color: "var(--text-primary)" }}>{c.name}</h3>
                  {c.domain && (
                    <a
                      href={`https://${c.domain}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontSize: "12px", color: "var(--accent-gold)", textDecoration: "none" }}
                    >
                      🌐 {c.domain}
                    </a>
                  )}
                </div>
                {c.industry && (
                  <span
                    style={{
                      background: "rgba(76,123,201,0.15)",
                      color: "#4c7bc9",
                      padding: "2px 8px",
                      borderRadius: "20px",
                      fontSize: "10px",
                      fontWeight: "700",
                      textTransform: "uppercase",
                    }}
                  >
                    {c.industry}
                  </span>
                )}
              </div>

              {c.research_summary ? (
                <div
                  style={{
                    background: "var(--bg-secondary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "8px",
                    padding: "10px 12px",
                    fontSize: "12px",
                    color: "var(--text-secondary)",
                    lineHeight: "1.4",
                  }}
                >
                  💡 <strong style={{ color: "var(--text-primary)" }}>AI Intelligence:</strong> {c.research_summary}
                </div>
              ) : (
                <p style={{ fontSize: "12px", color: "var(--text-muted)", fontStyle: "italic" }}>
                  Pending deep research
                </p>
              )}

              <div style={{ display: "flex", gap: "12px", fontSize: "11px", color: "var(--text-muted)", marginTop: "auto" }}>
                {c.country && <span>📍 {c.country}</span>}
                {c.size && <span>👥 {c.size} employees</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
