"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  Calendar,
  ChevronDown,
  ChevronUp,
  Inbox,
  Mail,
  MessageSquare,
  Send,
  Sparkles,
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
  subject: string;
  body: string;
  from_email: string;
  sent_at: string;
  created_at?: string;
  is_auto_generated: boolean;
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
  active: { label: "Active", color: "#4c7bc9" },
  awaiting_reply: { label: "Awaiting Reply", color: "#c9a84c" },
  reply_received: { label: "Reply Received", color: "#9c4cc9" },
  escalated: { label: "🔴 Escalated", color: "#c94c4c" },
  human_engaged: { label: "👤 Human Engaged", color: "#4cb89c" },
  closed: { label: "Closed", color: "#5a5a72" },
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
  const [filter, setFilter] = useState<"all" | "escalated" | "daily_logs">(showEscalated ? "escalated" : "daily_logs");

  // Selected Thread detail state
  const [selectedConv, setSelectedConv] = useState<any | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [copilot, setCopilot] = useState<CopilotDossier | null>(null);
  const [loadingCopilot, setLoadingCopilot] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [replySubject, setReplySubject] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      // Always fetch daily outreach logs
      const logsData = await apiFetch("/api/v1/conversations/daily-outreach-logs");
      const dates = logsData.dates || [];
      setDailyLogs(dates);

      // Auto expand all dates so sent messages are immediately visible
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

  useEffect(() => { load(); }, [filter]);

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

  const handleTakeover = async (id: string) => {
    try {
      await apiFetch(`/api/v1/conversations/${id}/takeover`, { method: "POST" });
      openThread({ ...selectedConv, id });
      load();
    } catch (e) {
      alert("Takeover failed: " + e);
    }
  };

  const handleReturnToAI = async (id: string) => {
    try {
      await apiFetch(`/api/v1/conversations/${id}/return-to-ai`, { method: "POST" });
      openThread({ ...selectedConv, id });
      load();
    } catch (e) {
      alert("Failed to return to AI: " + e);
    }
  };

  const handleSendReply = async () => {
    if (!replyText.trim() || !selectedConv) return;
    try {
      await apiFetch(`/api/v1/conversations/${selectedConv.id}/reply`, {
        method: "POST",
        body: JSON.stringify({ subject: replySubject, body: replyText }),
      });
      alert("Reply queued and sent!");
      openThread(selectedConv);
      load();
    } catch (e) {
      alert("Send failed: " + e);
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

  return (
    <div style={{ padding: "32px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "20px", fontWeight: "800", letterSpacing: "-0.02em", marginBottom: "4px" }}>
            Inbox & Conversations
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            Active prospect threads, intent analysis, and AI Copilot assistance
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          {[
            { id: "all", label: "All Threads", icon: Inbox },
            { id: "escalated", label: "Needs Human Handoff", icon: AlertTriangle },
            { id: "daily_logs", label: "Daily Sent Outreach Logs", icon: Calendar },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id as any)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  border: filter === tab.id ? "1px solid var(--rayven-accent)" : "1px solid var(--border)",
                  background: filter === tab.id ? "var(--rayven-accent-muted)" : "transparent",
                  color: filter === tab.id ? "var(--rayven-accent)" : "var(--text-secondary)",
                  fontSize: "12px",
                  fontWeight: "700",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  transition: "all 0.15s",
                }}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px" }}>
          Loading outreach logs & conversations...
        </div>
      ) : filter === "daily_logs" ? (
        /* Daily Outreach Logs View (Expandable/Collapsible Date Accordions) */
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {dailyLogs.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "64px 24px",
                background: "var(--bg-card)",
                border: "1px dashed var(--border)",
                borderRadius: "12px",
              }}
            >
              <div style={{ fontSize: "36px", marginBottom: "12px" }}>📅</div>
              <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>
                No daily outreach records found
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                Daily sent emails and prospect replies will be tracked here automatically.
              </p>
            </div>
          ) : (
            dailyLogs.map((group) => {
              const isExpanded = !!expandedDates[group.date];
              return (
                <div
                  key={group.date}
                  style={{
                    background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
                    border: "1px solid var(--border, #2a2a3c)",
                    borderRadius: "14px",
                    overflow: "hidden",
                    boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
                  }}
                >
                  {/* Date Accordion Header Bar */}
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
                      <span style={{ fontSize: "18px" }}>📅</span>
                      <div>
                        <h3 style={{ fontSize: "15px", fontWeight: "800", color: "#ffffff", margin: 0 }}>
                          {group.date_display}
                        </h3>
                        <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                          Total Activity: <strong>{group.total_sent} Sent Out</strong> · <strong>{group.total_replies} Replies Received</strong>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span
                        style={{
                          background: "rgba(201,168,76,0.15)",
                          color: "#c9a84c",
                          padding: "4px 12px",
                          borderRadius: "20px",
                          fontSize: "11px",
                          fontWeight: "800",
                        }}
                      >
                        {group.messages.length} Messages
                      </span>
                      <span style={{ fontSize: "16px", color: "#94a3b8", fontWeight: "700" }}>
                        {isExpanded ? "▲ Retract" : "▼ Expand"}
                      </span>
                    </div>
                  </div>

                  {/* Expanded List of Messages */}
                  {isExpanded && (
                    <div style={{ padding: "16px 22px", display: "flex", flexDirection: "column", gap: "12px" }}>
                      {group.messages.map((m: any) => {
                        const isOutbound = m.direction === "outbound";
                        const isReply = m.direction === "inbound";

                        return (
                          <div
                            key={m.id}
                            style={{
                              background: isOutbound ? "rgba(201,168,76,0.06)" : "rgba(56,189,248,0.08)",
                              border: `1px solid ${isOutbound ? "rgba(201,168,76,0.25)" : "rgba(56,189,248,0.3)"}`,
                              borderRadius: "12px",
                              padding: "16px",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                              <div>
                                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                                  <span
                                    style={{
                                      background: isOutbound ? "rgba(201,168,76,0.2)" : "rgba(56,189,248,0.2)",
                                      color: isOutbound ? "#c9a84c" : "#38bdf8",
                                      padding: "2px 10px",
                                      borderRadius: "12px",
                                      fontSize: "10px",
                                      fontWeight: "800",
                                      textTransform: "uppercase",
                                    }}
                                  >
                                    {isOutbound ? "📤 SENT OUTREACH" : "📥 PROSPECT REPLY"}
                                  </span>
                                  <span style={{ fontSize: "13px", fontWeight: "800", color: "#ffffff" }}>
                                    {m.prospect_name}
                                  </span>
                                  <span style={{ fontSize: "11px", color: "var(--accent-gold)", fontWeight: "600" }}>
                                    ({m.prospect_title || "Executive"})
                                  </span>
                                </div>
                                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                                  Company: {m.company_name} · Recipient: {m.to_email || "prospect@enterprise.com"}
                                </div>
                              </div>

                              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                                {m.sent_at ? new Date(m.sent_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                              </span>
                            </div>

                            {/* Subject & Body */}
                            <div style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: "8px", padding: "12px", marginTop: "8px" }}>
                              <div style={{ fontSize: "12px", fontWeight: "800", color: "#ffffff", marginBottom: "4px" }}>
                                Subject: {m.subject}
                              </div>
                              <div style={{ fontSize: "12px", color: "#e2e8f0", lineHeight: "1.5", whiteSpace: "pre-wrap" }}>
                                {m.body}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      ) : conversations.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "64px 24px",
            background: "var(--bg-card)",
            border: "1px dashed var(--border)",
            borderRadius: "12px",
          }}
        >
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>◎</div>
          <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>
            {filter === "escalated" ? "No escalated conversations" : "No conversations yet"}
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            {filter === "escalated"
              ? "All clear — no warm leads currently require human intervention."
              : "Conversations will appear here once outreach begins and prospects reply."}
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {conversations.map((conv) => {
            const statusInfo = STATUS_LABEL[conv.status] || { label: conv.status, color: "#5a5a72" };
            const isEscalated = conv.status === "escalated" || conv.status === "human_engaged";
            return (
              <div
                key={conv.id}
                style={{
                  background: "var(--bg-card)",
                  border: `1px solid ${isEscalated ? "rgba(201,76,76,0.4)" : "var(--border)"}`,
                  borderRadius: "12px",
                  padding: "18px 22px",
                  display: "flex",
                  alignItems: "center",
                  gap: "16px",
                  cursor: "pointer",
                }}
                onClick={() => openThread(conv)}
              >
                <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: statusInfo.color, flexShrink: 0 }} />

                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                    <span style={{ fontSize: "14px", fontWeight: "600" }}>{conv.subject || "No subject"}</span>
                    <span style={{ fontSize: "10px", fontWeight: "700", color: statusInfo.color, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {statusInfo.label}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>💬 {conv.message_count} messages</span>
                    {conv.last_reply_intent && (
                      <span style={{ fontSize: "12px", color: "var(--accent-gold)", fontWeight: "600" }}>
                        Intent: {conv.last_reply_intent.toUpperCase()}
                      </span>
                    )}
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>{new Date(conv.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px" }} onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => openThread(conv)}
                    style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", border: "none", borderRadius: "7px", padding: "6px 14px", color: "#0a0a0f", fontSize: "11px", fontWeight: "700", cursor: "pointer" }}
                  >
                    Open Thread & Copilot →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Full Thread & AI Copilot Panel Modal */}
      {selectedConv && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 100, padding: "24px" }}>
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "16px", width: "100%", maxWidth: "1000px", height: "90vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* Modal Header */}
            <div style={{ padding: "16px 24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--bg-secondary)" }}>
              <div>
                <h2 style={{ fontSize: "16px", fontWeight: "800" }}>{selectedConv.subject || "Conversation Thread"}</h2>
                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>ID: {selectedConv.id}</span>
              </div>
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                {selectedConv.ai_auto_respond ? (
                  <button onClick={() => handleTakeover(selectedConv.id)} style={{ background: "rgba(201,76,76,0.15)", border: "1px solid #c94c4c", color: "#ff6b6b", borderRadius: "8px", padding: "6px 14px", fontSize: "12px", fontWeight: "700", cursor: "pointer" }}>
                    👤 TAKE OVER
                  </button>
                ) : (
                  <button onClick={() => handleReturnToAI(selectedConv.id)} style={{ background: "rgba(76,184,156,0.15)", border: "1px solid #4cb89c", color: "#4cb89c", borderRadius: "8px", padding: "6px 14px", fontSize: "12px", fontWeight: "700", cursor: "pointer" }}>
                    🤖 RETURN TO AI
                  </button>
                )}
                <button onClick={() => handleResolve(selectedConv.id)} style={{ background: "var(--bg-hover)", border: "1px solid var(--border)", color: "var(--text-secondary)", borderRadius: "8px", padding: "6px 12px", fontSize: "12px", cursor: "pointer" }}>
                  Resolve
                </button>
                <button onClick={() => setSelectedConv(null)} style={{ background: "transparent", border: "none", color: "var(--text-muted)", fontSize: "20px", cursor: "pointer" }}>
                  ×
                </button>
              </div>
            </div>

            {/* Main split view: Left Messages, Right AI Copilot */}
            <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
              {/* Left Column: Messages & Composer */}
              <div style={{ flex: 1, display: "flex", flexDirection: "column", borderRight: "1px solid var(--border)", overflow: "hidden" }}>
                {/* Messages stream */}
                <div style={{ flex: 1, overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
                  {messages.map((m) => {
                    const isInbound = m.direction === "inbound";
                    return (
                      <div
                        key={m.id}
                        style={{
                          alignSelf: isInbound ? "flex-start" : "flex-end",
                          maxWidth: "80%",
                          background: isInbound ? "rgba(76,123,201,0.12)" : "rgba(201,168,76,0.12)",
                          border: `1px solid ${isInbound ? "rgba(76,123,201,0.3)" : "rgba(201,168,76,0.3)"}`,
                          borderRadius: "12px",
                          padding: "14px 16px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", fontSize: "11px", fontWeight: "700", color: isInbound ? "#4c7bc9" : "var(--accent-gold)" }}>
                          <span>{isInbound ? `📥 Prospect (${m.from_email})` : `📤 Rayven Outbound ${m.is_auto_generated ? "(AI Auto)" : "(Human)"}`}</span>
                          <span style={{ color: "var(--text-muted)", fontWeight: "400" }}>{m.sent_at ? new Date(m.sent_at).toLocaleString() : ""}</span>
                        </div>
                        <div style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: "1.5", whiteSpace: "pre-wrap" }}>
                          {m.body}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Reply Composer */}
                <div style={{ padding: "16px", borderTop: "1px solid var(--border)", background: "var(--bg-secondary)" }}>
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Write custom reply or select an AI Copilot response on the right..."
                    rows={4}
                    style={{ width: "100%", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", color: "var(--text-primary)", fontSize: "13px", resize: "none", outline: "none", marginBottom: "10px" }}
                  />
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                      {selectedConv.ai_auto_respond ? "⚠️ AI Auto-Respond active" : "👤 Human Takeover mode active"}
                    </span>
                    <button
                      onClick={handleSendReply}
                      disabled={!replyText.trim()}
                      style={{ background: "linear-gradient(135deg, #c9a84c, #a87830)", color: "#0a0a0f", border: "none", borderRadius: "8px", padding: "8px 20px", fontSize: "13px", fontWeight: "700", cursor: replyText.trim() ? "pointer" : "not-allowed" }}
                    >
                      Send Reply
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Column: AI Copilot Panel */}
              <div style={{ width: "380px", minWidth: "380px", background: "var(--bg-secondary)", padding: "20px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ fontSize: "13px", fontWeight: "800", color: "var(--accent-gold)", letterSpacing: "0.06em", textTransform: "uppercase", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "8px" }}>
                  🤖 AI Copilot Intelligence
                </div>

                {loadingCopilot ? (
                  <div style={{ color: "var(--text-muted)", fontSize: "12px", textAlign: "center", padding: "24px" }}>
                    Analyzing thread & KB evidence...
                  </div>
                ) : copilot ? (
                  <>
                    {/* Summary */}
                    <div>
                      <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>Summary</div>
                      <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4" }}>{copilot.conversation_summary}</p>
                    </div>

                    {/* Recommended Reply Variations */}
                    {copilot.recommended_replies.length > 0 && (
                      <div>
                        <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>Recommended Replies</div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                          {copilot.recommended_replies.map((r, i) => (
                            <div
                              key={i}
                              style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "8px", padding: "10px 12px", cursor: "pointer" }}
                              onClick={() => {
                                setReplySubject(r.subject);
                                setReplyText(r.body);
                              }}
                            >
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                <span style={{ fontSize: "11px", fontWeight: "700", color: "var(--accent-gold)" }}>{r.tone}</span>
                                <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>Click to Use →</span>
                              </div>
                              <p style={{ fontSize: "11px", color: "var(--text-secondary)", lineHeight: "1.3" }}>{r.body.slice(0, 100)}...</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Objection Handling */}
                    {copilot.objection_handling && (
                      <div style={{ background: "rgba(201,168,76,0.08)", border: "1px solid rgba(201,168,76,0.2)", borderRadius: "8px", padding: "10px 12px" }}>
                        <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--accent-gold)", marginBottom: "4px" }}>💡 Strategy / Objection Handling</div>
                        <p style={{ fontSize: "11px", color: "var(--text-secondary)", lineHeight: "1.4" }}>{copilot.objection_handling}</p>
                      </div>
                    )}

                    {/* Meeting Prep Questions */}
                    {copilot.meeting_prep_questions?.length > 0 && (
                      <div>
                        <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Meeting Prep Questions</div>
                        <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "11px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                          {copilot.meeting_prep_questions.map((q, i) => (
                            <li key={i}>{q}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Relevant Rayven Services */}
                    {copilot.relevant_rayven_services?.length > 0 && (
                      <div>
                        <div style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>Relevant Framework Services</div>
                        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                          {copilot.relevant_rayven_services.map((s, i) => (
                            <span key={i} style={{ background: "rgba(76,123,201,0.15)", color: "#4c7bc9", padding: "2px 8px", borderRadius: "12px", fontSize: "10px", fontWeight: "700" }}>
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>No copilot analysis available.</div>
                )}
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
    <Suspense fallback={<div style={{ padding: "48px", color: "var(--text-muted)", textAlign: "center" }}>Loading inbox...</div>}>
      <ConversationsInner />
    </Suspense>
  );
}
