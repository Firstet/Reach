"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: "⬡" },
  { href: "/dashboard/crm", label: "CRM Board", icon: "📊" },
  { href: "/dashboard/campaigns", label: "Campaigns", icon: "◈" },
  { href: "/dashboard/approvals", label: "Approvals", icon: "✉" },
  { href: "/dashboard/leads", label: "Pipeline", icon: "◉" },
  { href: "/dashboard/companies", label: "Companies", icon: "🏢" },
  { href: "/dashboard/conversations", label: "Inbox", icon: "◎" },
  { href: "/dashboard/templates", label: "Templates", icon: "📑" },
  { href: "/dashboard/knowledge", label: "Knowledge", icon: "◫" },
  { href: "/dashboard/suppression", label: "Blocklist", icon: "🛡️" },
  { href: "/dashboard/audit", label: "Audit Log", icon: "◳" },
  { href: "/dashboard/config", label: "Settings", icon: "⚙" },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<{ name: string; email: string; role: string } | null>(null);
  const [killSwitchActive, setKillSwitchActive] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    const userData = localStorage.getItem("user");
    if (userData) setUser(JSON.parse(userData));

    // Fetch kill switch status
    fetch("/api/v1/safety/kill-switch", { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.json())
      .then((data) => setKillSwitchActive(data.kill_switch_active))
      .catch(() => {});
  }, [router]);

  const toggleKillSwitch = async () => {
    const nextState = !killSwitchActive;
    if (nextState && !confirm("⚠️ DANGER: Activate Global Kill Switch? This will IMMEDIATELY halt ALL outbound campaign activity across the platform.")) {
      return;
    }
    const token = localStorage.getItem("access_token");
    try {
      await fetch(`/api/v1/safety/kill-switch?active=${nextState}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setKillSwitchActive(nextState);
    } catch {
      alert("Failed to toggle kill switch");
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    router.push("/login");
  };

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "220px",
          minWidth: "220px",
          background: "var(--bg-secondary)",
          borderRight: "1px solid var(--border)",
          display: "flex",
          flexDirection: "column",
          padding: "0",
          overflow: "hidden",
        }}
      >
        {/* Logo */}
        <div
          style={{
            padding: "20px 20px 16px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "30px",
                height: "30px",
                background: "linear-gradient(135deg, #c9a84c, #a87830)",
                borderRadius: "7px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "15px",
                fontWeight: "900",
                color: "#0a0a0f",
                flexShrink: 0,
              }}
            >
              R
            </div>
            <div>
              <div style={{ fontSize: "15px", fontWeight: "800", lineHeight: "1", letterSpacing: "-0.01em" }}>
                Reach
              </div>
              <div style={{ fontSize: "9px", color: "var(--accent-gold)", fontWeight: "600", letterSpacing: "0.08em", marginTop: "2px" }}>
                RAYVENSC
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: "12px 10px", overflowY: "auto" }}>
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "9px 12px",
                  borderRadius: "8px",
                  marginBottom: "2px",
                  textDecoration: "none",
                  background: active ? "rgba(201,168,76,0.12)" : "transparent",
                  color: active ? "var(--accent-gold)" : "var(--text-secondary)",
                  fontSize: "13px",
                  fontWeight: active ? "600" : "400",
                  transition: "all 0.15s",
                  borderLeft: active ? "2px solid var(--accent-gold)" : "2px solid transparent",
                }}
              >
                <span style={{ fontSize: "14px", width: "16px", textAlign: "center" }}>
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div
          style={{
            padding: "14px",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "10px",
            }}
          >
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                background: "linear-gradient(135deg, #2a2a38, #3a3a50)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "13px",
                fontWeight: "700",
                color: "var(--accent-gold)",
                flexShrink: 0,
              }}
            >
              {user?.name?.charAt(0) || "A"}
            </div>
            <div style={{ overflow: "hidden" }}>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: "600",
                  color: "var(--text-primary)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {user?.name || "Admin"}
              </div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "capitalize" }}>
                {user?.role || "admin"}
              </div>
            </div>
          </div>
          <button
            onClick={toggleKillSwitch}
            style={{
              width: "100%",
              background: killSwitchActive ? "rgba(201,76,76,0.2)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${killSwitchActive ? "#c94c4c" : "var(--border)"}`,
              borderRadius: "6px",
              padding: "7px",
              color: killSwitchActive ? "#ff6b6b" : "var(--text-muted)",
              fontSize: "11px",
              fontWeight: "700",
              cursor: "pointer",
              marginBottom: "8px",
              letterSpacing: "0.03em",
              transition: "all 0.15s",
            }}
          >
            {killSwitchActive ? "🛑 KILL SWITCH ACTIVE" : "⚡ Global Kill Switch"}
          </button>
          <button
            onClick={handleLogout}
            style={{
              width: "100%",
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: "6px",
              padding: "7px",
              color: "var(--text-muted)",
              fontSize: "11px",
              cursor: "pointer",
              transition: "all 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--accent-gold)";
              e.currentTarget.style.color = "var(--accent-gold)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.color = "var(--text-muted)";
            }}
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main
        style={{
          flex: 1,
          overflow: "auto",
          background: "var(--bg-primary)",
        }}
      >
        {children}
      </main>
    </div>
  );
}
