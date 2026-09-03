"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export interface ToastItem {
  id: string;
  type: "success" | "error" | "info" | "warning";
  message: string;
  duration?: number;
}

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel?: () => void;
}

interface ToastContextType {
  toast: {
    success: (msg: string, duration?: number) => void;
    error: (msg: string, duration?: number) => void;
    info: (msg: string, duration?: number) => void;
    warning: (msg: string, duration?: number) => void;
  };
  confirm: (opts: ConfirmOptions) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return {
      toast: {
        success: (msg: string) => console.log("[Success Toast]", msg),
        error: (msg: string) => console.error("[Error Toast]", msg),
        info: (msg: string) => console.log("[Info Toast]", msg),
        warning: (msg: string) => console.warn("[Warning Toast]", msg),
      },
      confirm: (opts: ConfirmOptions) => {
        if (window.confirm(opts.message)) opts.onConfirm();
        else if (opts.onCancel) opts.onCancel();
      },
    };
  }
  return ctx;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [confirmModal, setConfirmModal] = useState<ConfirmOptions | null>(null);

  const addToast = (type: ToastItem["type"], message: string, duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message, duration }]);
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const toastHelpers = {
    success: (msg: string, duration?: number) => addToast("success", msg, duration),
    error: (msg: string, duration?: number) => addToast("error", msg, duration),
    info: (msg: string, duration?: number) => addToast("info", msg, duration),
    warning: (msg: string, duration?: number) => addToast("warning", msg, duration),
  };

  const showConfirm = (opts: ConfirmOptions) => {
    setConfirmModal(opts);
  };

  // Override window.alert globally so native browser alert popups never display
  useEffect(() => {
    const originalAlert = window.alert;
    window.alert = (msg?: any) => {
      const strMsg = String(msg ?? "");
      if (
        strMsg.toLowerCase().includes("fail") ||
        strMsg.toLowerCase().includes("error") ||
        strMsg.toLowerCase().includes("invalid")
      ) {
        addToast("error", strMsg);
      } else if (
        strMsg.toLowerCase().includes("success") ||
        strMsg.toLowerCase().includes("complete") ||
        strMsg.toLowerCase().includes("triggered") ||
        strMsg.toLowerCase().includes("saved")
      ) {
        addToast("success", strMsg);
      } else {
        addToast("info", strMsg);
      }
    };

    return () => {
      window.alert = originalAlert;
    };
  }, []);

  return (
    <ToastContext.Provider value={{ toast: toastHelpers, confirm: showConfirm }}>
      {children}

      {/* Toast Notification Stack Container */}
      <div
        style={{
          position: "fixed",
          top: "20px",
          right: "20px",
          zIndex: 99999,
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          maxWidth: "420px",
          width: "calc(100vw - 40px)",
          pointerEvents: "none",
        }}
      >
        {toasts.map((t) => {
          const isSuccess = t.type === "success";
          const isError = t.type === "error";
          const isWarning = t.type === "warning";

          const borderColor = isSuccess
            ? "#34d399"
            : isError
            ? "#f87171"
            : isWarning
            ? "#fbbf24"
            : "#c9a84c";

          const icon = isSuccess ? "✓" : isError ? "✕" : isWarning ? "⚠" : "ℹ";

          const bgGradient = isSuccess
            ? "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(10, 15, 25, 0.95) 100%)"
            : isError
            ? "linear-gradient(135deg, rgba(239, 68, 68, 0.18) 0%, rgba(15, 10, 15, 0.95) 100%)"
            : isWarning
            ? "linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(20, 15, 10, 0.95) 100%)"
            : "linear-gradient(135deg, rgba(201, 168, 76, 0.15) 0%, rgba(15, 17, 23, 0.95) 100%)";

          return (
            <div
              key={t.id}
              style={{
                pointerEvents: "auto",
                background: bgGradient,
                backdropFilter: "blur(16px)",
                WebkitBackdropFilter: "blur(16px)",
                border: `1px solid ${borderColor}40`,
                borderLeft: `4px solid ${borderColor}`,
                borderRadius: "12px",
                padding: "14px 18px",
                boxShadow: "0 12px 32px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0,0,0,0.3)",
                display: "flex",
                alignItems: "flex-start",
                gap: "12px",
                color: "#ffffff",
                animation: "toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                position: "relative",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: "24px",
                  height: "24px",
                  borderRadius: "50%",
                  background: `${borderColor}25`,
                  color: borderColor,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "12px",
                  fontWeight: "900",
                  flexShrink: 0,
                  marginTop: "1px",
                }}
              >
                {icon}
              </div>

              <div style={{ flex: 1, fontSize: "13px", lineHeight: "1.5", fontWeight: "500", color: "#e2e8f0" }}>
                {t.message}
              </div>

              <button
                onClick={() => removeToast(t.id)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#94a3b8",
                  fontSize: "16px",
                  cursor: "pointer",
                  padding: "0 4px",
                  lineHeight: 1,
                  opacity: 0.7,
                  transition: "opacity 0.2s ease",
                }}
                onMouseEnter={(e) => ((e.target as HTMLElement).style.opacity = "1")}
                onMouseLeave={(e) => ((e.target as HTMLElement).style.opacity = "0.7")}
              >
                ×
              </button>

              <style>{`
                @keyframes toastSlideIn {
                  from {
                    transform: translateX(100%) scale(0.9);
                    opacity: 0;
                  }
                  to {
                    transform: translateX(0) scale(1);
                    opacity: 1;
                  }
                }
              `}</style>
            </div>
          );
        })}
      </div>

      {/* Branded Confirmation Modal */}
      {confirmModal && (
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
            zIndex: 999999,
            padding: "24px",
            animation: "modalFadeIn 0.2s ease-out",
          }}
        >
          <div
            style={{
              background: "linear-gradient(145deg, #12141f 0%, #0a0b12 100%)",
              border: "1px solid rgba(201, 168, 76, 0.3)",
              borderRadius: "16px",
              padding: "28px",
              maxWidth: "460px",
              width: "100%",
              boxShadow: "0 24px 48px rgba(0, 0, 0, 0.8), 0 0 30px rgba(201, 168, 76, 0.1)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, rgba(201,168,76,0.2), rgba(168,120,48,0.1))",
                  border: "1px solid var(--accent-gold, #c9a84c)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "16px",
                }}
              >
                ⚖️
              </div>
              <h3 style={{ fontSize: "17px", fontWeight: "800", color: "#ffffff", letterSpacing: "-0.01em" }}>
                {confirmModal.title || "Confirm Action"}
              </h3>
            </div>

            <p style={{ fontSize: "14px", color: "#94a3b8", lineHeight: "1.6", marginBottom: "24px" }}>
              {confirmModal.message}
            </p>

            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
              <button
                onClick={() => {
                  if (confirmModal.onCancel) confirmModal.onCancel();
                  setConfirmModal(null);
                }}
                style={{
                  background: "transparent",
                  border: "1px solid var(--border, rgba(255,255,255,0.15))",
                  color: "#94a3b8",
                  borderRadius: "8px",
                  padding: "10px 18px",
                  fontSize: "13px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                {confirmModal.cancelText || "Cancel"}
              </button>

              <button
                onClick={() => {
                  confirmModal.onConfirm();
                  setConfirmModal(null);
                }}
                style={{
                  background: "linear-gradient(135deg, #c9a84c 0%, #a87830 100%)",
                  border: "none",
                  color: "#0a0a0f",
                  borderRadius: "8px",
                  padding: "10px 22px",
                  fontSize: "13px",
                  fontWeight: "800",
                  cursor: "pointer",
                  boxShadow: "0 4px 14px rgba(201, 168, 76, 0.25)",
                }}
              >
                {confirmModal.confirmText || "Confirm"}
              </button>
            </div>
          </div>
          <style>{`
            @keyframes modalFadeIn {
              from { opacity: 0; transform: scale(0.95); }
              to { opacity: 1; transform: scale(1); }
            }
          `}</style>
        </div>
      )}
    </ToastContext.Provider>
  );
}
