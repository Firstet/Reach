"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

import {
  BookOpen,
  Building2,
  CheckSquare,
  FileText,
  Inbox,
  Kanban,
  LayoutDashboard,
  LogOut,
  OctagonAlert,
  ScrollText,
  Send,
  Settings,
  ShieldBan,
  Users,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/crm", label: "CRM Board", icon: Kanban },
  { href: "/dashboard/campaigns", label: "Campaigns", icon: Send },
  { href: "/dashboard/approvals", label: "Approvals", icon: CheckSquare },
  { href: "/dashboard/leads", label: "Pipeline", icon: Users },
  { href: "/dashboard/companies", label: "Companies", icon: Building2 },
  { href: "/dashboard/conversations", label: "Inbox", icon: Inbox },
  { href: "/dashboard/templates", label: "Templates", icon: FileText },
  { href: "/dashboard/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/dashboard/suppression", label: "Blocklist", icon: ShieldBan },
  { href: "/dashboard/audit", label: "Audit Log", icon: ScrollText },
  { href: "/dashboard/config", label: "Settings", icon: Settings },
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
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: "var(--bg-primary)" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "230px",
          minWidth: "230px",
          background: "linear-gradient(180deg, #0b0d14 0%, #07080c 100%)",
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
            padding: "20px 18px 16px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <img
              src="/logo.svg"
              alt="RAYVEN AI Logo"
              style={{
                width: "34px",
                height: "34px",
                borderRadius: "8px",
                boxShadow: "0 0 12px var(--rayven-accent-glow)",
              }}
            />
            <div>
              <div style={{ fontSize: "16px", fontWeight: "900", lineHeight: "1", letterSpacing: "-0.02em", color: "#ffffff" }}>
                RAYVEN AI
              </div>
              <div style={{ fontSize: "10px", color: "var(--rayven-accent)", fontWeight: "700", letterSpacing: "0.06em", marginTop: "3px" }}>
                by RayvenSC
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: "12px 10px", overflowY: "auto" }}>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "11px",
                  padding: "9px 12px",
                  borderRadius: "8px",
                  marginBottom: "3px",
                  textDecoration: "none",
                  background: active ? "var(--rayven-accent-muted)" : "transparent",
                  color: active ? "#ffffff" : "var(--text-secondary)",
                  fontSize: "13px",
                  fontWeight: active ? "700" : "500",
                  transition: "all 0.15s ease",
                  borderLeft: active ? "3px solid var(--rayven-accent)" : "3px solid transparent",
                }}
              >
                <Icon
                  size={17}
                  style={{
                    color: active ? "var(--rayven-accent)" : "var(--text-muted)",
                    flexShrink: 0,
                  }}
                />
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
            background: "rgba(0,0,0,0.2)",
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
                background: "linear-gradient(135deg, #1b1e2e, #2a2e45)",
                border: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "13px",
                fontWeight: "800",
                color: "var(--rayven-accent)",
                flexShrink: 0,
              }}
            >
              {user?.name?.charAt(0) || "A"}
            </div>
            <div style={{ overflow: "hidden" }}>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: "700",
                  color: "#ffffff",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {user?.name || "Admin Operator"}
              </div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "capitalize" }}>
                {user?.role || "System Admin"}
              </div>
            </div>
          </div>
          <button
            onClick={toggleKillSwitch}
            style={{
              width: "100%",
              background: killSwitchActive ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${killSwitchActive ? "#ef4444" : "var(--border)"}`,
              borderRadius: "6px",
              padding: "7px",
              color: killSwitchActive ? "#f87171" : "var(--text-muted)",
              fontSize: "11px",
              fontWeight: "700",
              cursor: "pointer",
              marginBottom: "8px",
              letterSpacing: "0.03em",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              transition: "all 0.15s",
            }}
          >
            <OctagonAlert size={13} style={{ color: killSwitchActive ? "#ef4444" : "var(--text-muted)" }} />
            {killSwitchActive ? "STOPPED (KILL SWITCH)" : "Global Kill Switch"}
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
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              transition: "all 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--rayven-accent)";
              e.currentTarget.style.color = "var(--rayven-accent)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.color = "var(--text-muted)";
            }}
          >
            <LogOut size={13} />
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
