"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  Archive,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Inbox,
  Mail,
  MessageSquare,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  Trash2,
  User,
  UserCheck,
} from "lucide-react";

interface Conversation {
  id: string;
  lead_id: string;
  status: string;
  subject: string | null;
  last_reply_intent: string | null;
  escalated_at: string | null;
  human_engaged_at: string | null;
  message_count: number;
  updated_at: string;
}

interface MessageItem {
  id: string;
  direction: "inbound" | "outbound";
  status?: string;
  subject: string;
  body: string;
  from_email: string;
  to_email?: string;
  sent_at: string;
  created_at?: string;
  is_auto_generated: boolean;
  prospect_name?: string;
  prospect_title?: string;
  company_name?: string;
}

interface CopilotDossier {
  conversation_summary: string;
  recommended_replies: Array<{ tone: string; subject: string; body: string }>;
  objection_handling: string;
  meeting_prep_questions: string[];
  relevant_rayven_services: string[];
  key_insights: string;
}

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  inactive: { label: "Inactive", color: "#5a5a72" },
  active: { label: "Active Inbox", color: "#38bdf8" },
  awaiting_reply: { label: "Awaiting Reply", color: "#c9a84c" },
  reply_received: { label: "Reply Received", color: "#9c4cc9" },
  escalated: { label: "🔴 Escalated Hot Lead", color: "#f43f5e" },
  human_engaged: { label: "👤 Human Engaged", color: "#10b981" },
  closed: { label: "Closed / Archived", color: "#5a5a72" },
};

async function apiFetch(path: string, opts?: RequestInit) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(path, {
    ...opts,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function ConversationsInner() {
  const searchParams = useSearchParams();
  const showEscalated = searchParams.get("escalated") === "true";
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [dailyLogs, setDailyLogs] = useState<any[]>([]);
  const [expandedDates, setExpandedDates] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [filter, setFilter] = useState<"inbox" | "sent" | "escalated" | "daily_logs">(
    showEscalated ? "escalated" : "inbox"
  );
  const [searchQuery, setSearchQuery] = useState("");

  // Selected Thread detail modal state
  const [selectedConv, setSelectedConv] = useState<any | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<MessageItem | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [copilot, setCopilot] = useState<CopilotDossier | null>(null);
  const [loadingCopilot, setLoadingCopilot] = useState(false);
  const [sendingReply, setSendingReply] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [replySubject, setReplySubject] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      // Always fetch daily outreach & message logs
      const logsData = await apiFetch("/api/v1/conversations/daily-outreach-logs");
      const dates = logsData.dates || [];
      setDailyLogs(dates);

      // Auto expand all dates
      const expanded: Record<string, boolean> = {};
      for (const d of dates) {
        expanded[d.date] = true;
      }
      setExpandedDates(expanded);

      if (filter !== "daily_logs") {
        const q = filter === "escalated" ? "?escalated_only=true" : "?page_size=50";
        const data = await apiFetch(`/api/v1/conversations${q}`);
        setConversations(data.items || []);
      }
    } catch {
      /* not connected */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filter]);

  const handleSyncMailbox = async () => {
    setSyncing(true);
    try {
      const res = await apiFetch("/api/v1/conversations/sync", { method: "POST" });
      alert(`⚡ Mailbox Synchronization Complete!\nProcessed ${res.processed || 0} incoming/outgoing messages.`);
      await load();
    } catch (e: any) {
      alert("Mailbox Sync Note: " + (e?.message || e));
    } finally {
      setSyncing(false);
    }
  };

  const toggleDateAccordion = (dateKey: string) => {
    setExpandedDates((prev) => ({ ...prev, [dateKey]: !prev[dateKey] }));
  };

  const openThread = async (conv: Conversation) => {
    try {
      const data = await apiFetch(`/api/v1/conversations/${conv.id}`);
      setSelectedConv(data);
      setMessages(data.messages || []);
      setReplySubject(data.subject ? `Re: ${data.subject}` : "Re: Strategic Communications");
      setReplyText("");

      // Fetch AI Copilot dossier
      setLoadingCopilot(true);
      try {
        const copilotData = await apiFetch(`/api/v1/conversations/${conv.id}/copilot`);
        setCopilot(copilotData);
      } catch {
        setCopilot(null);
      } finally {
        setLoadingCopilot(false);
      }
    } catch (e) {
      alert("Failed to load thread details: " + e);
    }
  };

  const openMessageModal = (msg: MessageItem) => {
    setSelectedMessage(msg);
    setReplySubject(msg.subject ? (msg.subject.startsWith("Re:") ? msg.subject : `Re: ${msg.subject}`) : "Re: Strategic Communications");
    setReplyText("");
  };

  const handleSendReply = async () => {
    if (!replyText.trim()) return;
    setSendingReply(true);
    try {
      let targetConvId = selectedConv?.id;
      if (!targetConvId && selectedMessage) {
        // Find matching conversation or fetch list
        const convList = await apiFetch("/api/v1/conversations?page_size=50");
        if (convList.items?.length > 0) {
          targetConvId = convList.items[0].id;
        }
      }

      if (!targetConvId) {
        alert("Select an active thread or prospect conversation to reply.");
        return;
      }

      const res = await apiFetch(`/api/v1/conversations/${targetConvId}/reply`, {
        method: "POST",
        body: JSON.stringify({ subject: replySubject, body: replyText }),
      });

      alert(`✅ Email Dispatched Successfully!\nSent to prospect email: ${res.to_email || "Recipient"}`);
      setReplyText("");
      setSelectedMessage(null);
      if (selectedConv) {
        openThread(selectedConv);
      }
      await load();
    } catch (e: any) {
      alert("Send failed: " + (e?.message || e));
    } finally {
      setSendingReply(false);
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await apiFetch(`/api/v1/conversations/${id}/resolve`, { method: "POST" });
      setSelectedConv(null);
      load();
    } catch {
      alert("Failed to resolve");
    }
  };

  // Extract all messages across dates for folder filtering
  const allFolderMessages = dailyLogs.flatMap((d) => d.messages || []);
  const inboundMessages = allFolderMessages.filter((m) => m.direction === "inbound");
  const outboundMessages = allFolderMessages.filter((m) => m.direction === "outbound");

  // Search filtering
  const filterBySearch = (msgList: any[]) => {
    if (!searchQuery.trim()) return msgList;
    const q = searchQuery.toLowerCase();
    return msgList.filter(
      (m) =>
        (m.subject || "").toLowerCase().includes(q) ||
        (m.body || "").toLowerCase().includes(q) ||
        (m.prospect_name || "").toLowerCase().includes(q) ||
        (m.company_name || "").toLowerCase().includes(q) ||
        (m.from_email || "").toLowerCase().includes(q) ||
        (m.to_email || "").toLowerCase().includes(q)
    );
  };

  return (
    <div style={{ padding: "32px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* Header & Mailbox Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", gap: "16px", flexWrap: "wrap" }}>
        <div>
          <h1 style={{ fontSize: "22px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px", display: "flex", alignItems: "center", gap: "10px" }}>
            <Mail style={{ color: "var(--rayven-accent)" }} size={24} /> Email Inbox & Communications Synchronizer
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Full SMTP/IMAP connected mail client for RAYVEN AI. Synchronize inbox, sent dispatches, warm prospect threads, and reply live.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          {/* Search Box */}
          <div style={{ position: "relative", width: "260px" }}>
            <Search size={14} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search emails or prospects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: "100%",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "8px 12px 8px 34px",
                color: "#ffffff",
                fontSize: "12px",
                outline: "none",
              }}
            />
          </div>

          <button
            onClick={handleSyncMailbox}
            disabled={syncing}
            style={{
              background: syncing ? "rgba(201,168,76,0.15)" : "linear-gradient(135deg, #c9a84c 0%, #a87830 100%)",
              border: "1px solid #c9a84c",
              borderRadius: "8px",
              padding: "9px 18px",
              color: syncing ? "#c9a84c" : "#0a0a0f",
              fontSize: "12px",
              fontWeight: "800",
              cursor: syncing ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: "0 4px 12px rgba(201, 168, 76, 0.25)",
            }}
          >
            <RefreshCw size={14} className={syncing ? "animate-spin" : ""} />
            {syncing ? "Syncing IMAP Mailbox..." : "⚡ Sync Mailbox Now"}
          </button>
        </div>
      </div>

      {/* Folder Navigation Tabs */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "24px", borderBottom: "1px solid var(--border)", paddingBottom: "16px", flexWrap: "wrap" }}>
        {[
          { id: "inbox", label: "Inbox & Replies", icon: Inbox, count: inboundMessages.length },
          { id: "sent", label: "Sent Dispatches", icon: Send, count: outboundMessages.length },
          { id: "escalated", label: "Hot Lead Escalations", icon: AlertTriangle, count: conversations.filter((c) => c.status === "escalated").length },
          { id: "daily_logs", label: "Daily Timeline View", icon: Calendar, count: dailyLogs.length },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = filter === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as any)}
              style={{
                padding: "10px 18px",
                borderRadius: "8px",
                border: isActive ? "1px solid var(--rayven-accent)" : "1px solid var(--border)",
                background: isActive ? "var(--rayven-accent-muted)" : "rgba(255,255,255,0.02)",
                color: isActive ? "var(--rayven-accent)" : "var(--text-secondary)",
                fontSize: "13px",
                fontWeight: "700",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                transition: "all 0.15s",
              }}
            >
              <Icon size={15} />
              {tab.label}
              <span
                style={{
                  background: isActive ? "rgba(201,168,76,0.3)" : "rgba(255,255,255,0.06)",
                  color: isActive ? "#ffffff" : "var(--text-muted)",
                  borderRadius: "12px",
                  padding: "2px 8px",
                  fontSize: "11px",
                  fontWeight: "800",
                  marginLeft: "4px",
                }}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Main Mailbox Content */}
      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "64px" }}>
          Synchronizing emails & conversations...
        </div>
      ) : filter === "inbox" ? (
        /* INBOX VIEW */
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {filterBySearch(inboundMessages).length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "64px 24px",
                background: "var(--bg-card)",
                border: "1px dashed var(--border)",
                borderRadius: "12px",
              }}
            >
              <Inbox size={40} style={{ color: "var(--text-muted)", marginBottom: "12px" }} />
              <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>Your Inbox is Up to Date</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                Incoming prospect replies received via SMTP/IMAP will appear here automatically. Click "⚡ Sync Mailbox Now" to check for new messages.
              </p>
            </div>
          ) : (
            filterBySearch(inboundMessages).map((m: MessageItem) => (
              <div
                key={m.id}
                onClick={() => openMessageModal(m)}
                style={{
                  background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
                  border: "1px solid rgba(56,189,248,0.3)",
                  borderRadius: "12px",
                  padding: "18px 22px",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.2)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span style={{ background: "rgba(56,189,248,0.2)", color: "#38bdf8", padding: "3px 10px", borderRadius: "12px", fontSize: "10px", fontWeight: "800" }}>
                        📥 INCOMING PROSPECT REPLY
                      </span>
                      <span style={{ fontSize: "14px", fontWeight: "800", color: "#ffffff" }}>{m.prospect_name || m.from_email}</span>
                      <span style={{ fontSize: "12px", color: "var(--accent-gold)" }}>{m.company_name ? `· ${m.company_name}` : ""}</span>
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>From: {m.from_email}</div>
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {m.sent_at ? new Date(m.sent_at).toLocaleString() : "Recently Received"}
                  </span>
                </div>

                <div style={{ fontSize: "13px", fontWeight: "700", color: "#ffffff", marginBottom: "6px" }}>{m.subject}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.5", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                  {m.body}
                </div>

                <div style={{ marginTop: "12px", display: "flex", justifyContent: "flex-end" }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openMessageModal(m);
                    }}
                    style={{
                      background: "rgba(201,168,76,0.15)",
                      border: "1px solid #c9a84c",
                      borderRadius: "6px",
                      padding: "6px 14px",
                      color: "#c9a84c",
                      fontSize: "11px",
                      fontWeight: "800",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <Send size={12} /> Read & Reply Live
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      ) : filter === "sent" ? (
        /* SENT DISPATCHES VIEW */
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {filterBySearch(outboundMessages).length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "64px 24px",
                background: "var(--bg-card)",
                border: "1px dashed var(--border)",
                borderRadius: "12px",
              }}
            >
              <Send size={40} style={{ color: "var(--text-muted)", marginBottom: "12px" }} />
              <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>No Sent Dispatches Found</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                Outreach emails sent by RAYVEN AI or manual operator replies will be logged here.
              </p>
            </div>
          ) : (
            filterBySearch(outboundMessages).map((m: MessageItem) => (
              <div
                key={m.id}
                onClick={() => openMessageModal(m)}
                style={{
                  background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
                  border: "1px solid rgba(201,168,76,0.3)",
                  borderRadius: "12px",
                  padding: "18px 22px",
                  cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span style={{ background: "rgba(201,168,76,0.2)", color: "#c9a84c", padding: "3px 10px", borderRadius: "12px", fontSize: "10px", fontWeight: "800" }}>
                        📤 SENT DISPATCH
                      </span>
                      <span style={{ fontSize: "14px", fontWeight: "800", color: "#ffffff" }}>To: {m.prospect_name || m.to_email}</span>
                      <span style={{ fontSize: "12px", color: "var(--accent-gold)" }}>{m.company_name ? `· ${m.company_name}` : ""}</span>
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>Recipient: {m.to_email}</div>
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {m.sent_at ? new Date(m.sent_at).toLocaleString() : "Recently Sent"}
                  </span>
                </div>

                <div style={{ fontSize: "13px", fontWeight: "700", color: "#ffffff", marginBottom: "6px" }}>{m.subject}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.5", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                  {m.body}
                </div>
              </div>
            ))
          )}
        </div>
      ) : filter === "escalated" ? (
        /* HOT LEAD ESCALATIONS VIEW */
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {conversations.filter((c) => c.status === "escalated" || c.status === "human_engaged").length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "64px 24px",
                background: "var(--bg-card)",
                border: "1px dashed var(--border)",
                borderRadius: "12px",
              }}
            >
              <CheckCircle2 size={40} style={{ color: "#22c55e", marginBottom: "12px" }} />
              <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>No Hot Escalations Pending</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                All clear — no high-intent prospect threads currently require manual human handoff.
              </p>
            </div>
          ) : (
            conversations
              .filter((c) => c.status === "escalated" || c.status === "human_engaged")
              .map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => openThread(conv)}
                  style={{
                    background: "linear-gradient(145deg, #1f1214 0%, #120a0b 100%)",
                    border: "1px solid rgba(244,63,94,0.4)",
                    borderRadius: "12px",
                    padding: "18px 22px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span style={{ background: "rgba(244,63,94,0.2)", color: "#f43f5e", padding: "3px 10px", borderRadius: "12px", fontSize: "10px", fontWeight: "800" }}>
                        🔴 HIGH INTENT ESCALATION
                      </span>
                      <span style={{ fontSize: "14px", fontWeight: "800", color: "#ffffff" }}>{conv.subject || "Warm Prospect Thread"}</span>
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--accent-gold)", fontWeight: "600" }}>
                      Intent: {(conv.last_reply_intent || "MEETING_REQUEST").toUpperCase()} · Updated: {new Date(conv.updated_at).toLocaleString()}
                    </div>
                  </div>

                  <button
                    onClick={() => openThread(conv)}
                    style={{
                      background: "linear-gradient(135deg, #f43f5e 0%, #be123c 100%)",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "6px",
                      padding: "8px 16px",
                      fontSize: "12px",
                      fontWeight: "800",
                      cursor: "pointer",
                    }}
                  >
                    Open Thread & Takeover →
                  </button>
                </div>
              ))
          )}
        </div>
      ) : (
        /* DAILY TIMELINE VIEW */
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {dailyLogs.map((group) => {
            const isExpanded = !!expandedDates[group.date];
            return (
              <div
                key={group.date}
                style={{
                  background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
                  border: "1px solid var(--border, #2a2a3c)",
                  borderRadius: "14px",
                  overflow: "hidden",
                }}
              >
                <div
                  onClick={() => toggleDateAccordion(group.date)}
                  style={{
                    padding: "16px 22px",
                    background: "rgba(255,255,255,0.03)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    cursor: "pointer",
                    borderBottom: isExpanded ? "1px solid var(--border)" : "none",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <Calendar size={18} style={{ color: "var(--accent-gold)" }} />
                    <div>
                      <h3 style={{ fontSize: "15px", fontWeight: "800", color: "#ffffff", margin: 0 }}>{group.date_display}</h3>
                      <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                        Total Activity: <strong>{group.total_sent} Dispatched</strong> · <strong>{group.total_replies} Inbound Replies</strong>
                      </div>
                    </div>
                  </div>

                  <span style={{ fontSize: "11px", fontWeight: "800", color: "#c9a84c", background: "rgba(201,168,76,0.15)", padding: "4px 12px", borderRadius: "20px" }}>
                    {group.messages.length} Messages
                  </span>
                </div>

                {isExpanded && (
                  <div style={{ padding: "16px 22px", display: "flex", flexDirection: "column", gap: "12px" }}>
                    {group.messages.map((m: any) => (
                      <div
                        key={m.id}
                        onClick={() => openMessageModal(m)}
                        style={{
                          background: m.direction === "outbound" ? "rgba(201,168,76,0.06)" : "rgba(56,189,248,0.08)",
                          border: `1px solid ${m.direction === "outbound" ? "rgba(201,168,76,0.25)" : "rgba(56,189,248,0.3)"}`,
                          borderRadius: "10px",
                          padding: "14px 18px",
                          cursor: "pointer",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                          <span style={{ fontSize: "11px", fontWeight: "800", color: m.direction === "outbound" ? "#c9a84c" : "#38bdf8" }}>
                            {m.direction === "outbound" ? "📤 SENT OUTREACH" : "📥 PROSPECT REPLY"} ({m.prospect_name || m.to_email || m.from_email})
                          </span>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                            {m.sent_at ? new Date(m.sent_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                          </span>
                        </div>
                        <div style={{ fontSize: "13px", fontWeight: "700", color: "#ffffff", marginBottom: "4px" }}>Subject: {m.subject}</div>
                        <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.5", whiteSpace: "pre-wrap" }}>{m.body}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* READ & REPLY MANUAL EMAIL MODAL */}
      {(selectedMessage || selectedConv) && (
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
              maxWidth: "800px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 24px 48px rgba(0, 0, 0, 0.8)",
            }}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", borderBottom: "1px solid var(--border)", paddingBottom: "16px" }}>
              <div>
                <h2 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff", marginBottom: "4px" }}>
                  {selectedMessage?.subject || selectedConv?.subject || "Email Conversation Reader"}
                </h2>
                <div style={{ fontSize: "12px", color: "var(--accent-gold)", fontWeight: "600" }}>
                  Recipient: {selectedMessage?.to_email || selectedMessage?.from_email || "Prospect"}
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedMessage(null);
                  setSelectedConv(null);
                }}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "24px", cursor: "pointer" }}
              >
                ×
              </button>
            </div>

            {/* Email Message Content */}
            {selectedMessage && (
              <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)", borderRadius: "12px", padding: "20px", marginBottom: "24px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                  <div style={{ fontSize: "11px", fontWeight: "800", color: "var(--rayven-accent)", textTransform: "uppercase" }}>
                    From: {selectedMessage.from_email}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    {selectedMessage.sent_at ? new Date(selectedMessage.sent_at).toLocaleString() : ""}
                  </div>
                </div>

                <div style={{ fontSize: "13px", color: "#e2e8f0", lineHeight: "1.6", whiteSpace: "pre-wrap" }}>
                  {selectedMessage.body}
                </div>
              </div>
            )}

            {/* Full Thread Messages if conversation selected */}
            {selectedConv && messages.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "24px" }}>
                {messages.map((m) => (
                  <div
                    key={m.id}
                    style={{
                      background: m.direction === "outbound" ? "rgba(201,168,76,0.06)" : "rgba(56,189,248,0.08)",
                      border: `1px solid ${m.direction === "outbound" ? "rgba(201,168,76,0.25)" : "rgba(56,189,248,0.3)"}`,
                      borderRadius: "10px",
                      padding: "16px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "11px", fontWeight: "800", color: m.direction === "outbound" ? "#c9a84c" : "#38bdf8" }}>
                        {m.direction === "outbound" ? "📤 SENT" : "📥 RECEIVED"}
                      </span>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                        {m.sent_at ? new Date(m.sent_at).toLocaleString() : ""}
                      </span>
                    </div>
                    <div style={{ fontSize: "13px", color: "#e2e8f0", lineHeight: "1.6", whiteSpace: "pre-wrap" }}>
                      {m.body}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Manual Reply Form */}
            <div style={{ background: "rgba(201,168,76,0.06)", border: "1px solid rgba(201,168,76,0.25)", borderRadius: "12px", padding: "20px" }}>
              <h3 style={{ fontSize: "14px", fontWeight: "800", color: "#c9a84c", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <Send size={16} /> Reply to Prospect Directly via Live SMTP / Connected Email
              </h3>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                  Subject Line
                </label>
                <input
                  type="text"
                  value={replySubject}
                  onChange={(e) => setReplySubject(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(0,0,0,0.3)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    padding: "10px 14px",
                    color: "#ffffff",
                    fontSize: "13px",
                    outline: "none",
                  }}
                />
              </div>

              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                  Message Body
                </label>
                <textarea
                  rows={5}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Write your manual reply here..."
                  style={{
                    width: "100%",
                    background: "rgba(0,0,0,0.3)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    padding: "12px 14px",
                    color: "#ffffff",
                    fontSize: "13px",
                    outline: "none",
                    resize: "vertical",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
                <button
                  onClick={() => {
                    setSelectedMessage(null);
                    setSelectedConv(null);
                  }}
                  style={{ background: "transparent", border: "1px solid var(--border)", color: "#94a3b8", borderRadius: "8px", padding: "10px 18px", fontSize: "12px", cursor: "pointer" }}
                >
                  Cancel
                </button>

                <button
                  onClick={handleSendReply}
                  disabled={sendingReply || !replyText.trim()}
                  style={{
                    background: sendingReply ? "rgba(201,168,76,0.3)" : "linear-gradient(135deg, #c9a84c 0%, #a87830 100%)",
                    color: "#0a0a0f",
                    borderRadius: "8px",
                    padding: "10px 20px",
                    fontSize: "12px",
                    fontWeight: "800",
                    border: "none",
                    cursor: sendingReply ? "not-allowed" : "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <Send size={14} className={sendingReply ? "animate-spin" : ""} />
                  {sendingReply ? "Sending Email..." : "⚡ Send Live Email to Prospect"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ConversationsPage() {
  return (
    <Suspense fallback={<div style={{ padding: "32px", color: "var(--text-muted)" }}>Loading mailbox...</div>}>
      <ConversationsInner />
    </Suspense>
  );
}
