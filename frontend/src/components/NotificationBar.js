// PropIQ Notification Bar — In-app alert panel for CHM alerts
import React, { useState } from "react";

const RISK_CONFIG = {
  red: {
    color: "#DC2626",
    bg: "#FEF2F2",
    border: "#FCA5A5",
    icon: "🔴",
    label: "BREACH",
  },
  amber: {
    color: "#D97706",
    bg: "#FFFBEB",
    border: "#FCD34D",
    icon: "🟡",
    label: "WARNING",
  },
};

export default function NotificationBar({
  notifications,
  onDismiss,
  onClearAll,
}) {
  const [open, setOpen] = useState(false);
  const count = notifications.length;

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      {/* Bell Button */}
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          position: "relative",
          background: count > 0 ? "#1A1B26" : "transparent",
          border: count > 0 ? "1px solid #374151" : "1px solid transparent",
          borderRadius: 10,
          padding: "6px 12px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 8,
          transition: "all 0.2s",
        }}
        title="Collateral Health Alerts"
      >
        <span style={{ fontSize: 18, lineHeight: 1 }}>🔔</span>
        {count > 0 && (
          <span
            style={{
              position: "absolute",
              top: -6,
              right: -6,
              background: "#DC2626",
              color: "#fff",
              borderRadius: "50%",
              width: 18,
              height: 18,
              fontSize: 10,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "2px solid #0D0E15",
            }}
          >
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div
          style={{
            position: "absolute",
            top: "110%",
            right: 0,
            width: 360,
            background: "#fff",
            borderRadius: 14,
            boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
            border: "1px solid #E5E7EB",
            zIndex: 999,
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "14px 18px",
              borderBottom: "1px solid #F3F4F6",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: "#0D0E15",
            }}
          >
            <div>
              <div
                style={{
                  color: "#7C6FD8",
                  fontSize: 10,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                PropIQ Alerts
              </div>
              <div style={{ color: "#fff", fontSize: 14, fontWeight: 700 }}>
                {count === 0
                  ? "No active alerts"
                  : `${count} Collateral Alert${count > 1 ? "s" : ""}`}
              </div>
            </div>
            {count > 0 && (
              <button
                onClick={onClearAll}
                style={{
                  background: "transparent",
                  border: "1px solid #374151",
                  color: "#9CA3AF",
                  borderRadius: 6,
                  padding: "4px 10px",
                  cursor: "pointer",
                  fontSize: 11,
                }}
              >
                Clear All
              </button>
            )}
          </div>

          {/* Alert List */}
          <div style={{ maxHeight: 380, overflowY: "auto" }}>
            {count === 0 ? (
              <div
                style={{
                  padding: 32,
                  textAlign: "center",
                  color: "#9CA3AF",
                  fontSize: 13,
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
                All collaterals are healthy
              </div>
            ) : (
              notifications.map((notif, i) => {
                const rc = RISK_CONFIG[notif.risk_level] || RISK_CONFIG.amber;
                return (
                  <div
                    key={i}
                    style={{
                      padding: "14px 18px",
                      borderBottom: "1px solid #F9FAFB",
                      background: rc.bg,
                      borderLeft: `3px solid ${rc.color}`,
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          marginBottom: 4,
                        }}
                      >
                        <span
                          style={{
                            background: rc.color,
                            color: "#fff",
                            fontSize: 9,
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: 20,
                            letterSpacing: "0.06em",
                          }}
                        >
                          {rc.label}
                        </span>
                        <span
                          style={{
                            fontSize: 12,
                            fontWeight: 700,
                            color: "#111",
                          }}
                        >
                          {notif.loan_id}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: "#374151" }}>
                        <strong>{notif.locality}</strong> — LTV:{" "}
                        <strong style={{ color: rc.color }}>
                          {notif.ltv?.toFixed
                            ? notif.ltv.toFixed(1)
                            : notif.ltv}
                          %
                        </strong>
                      </div>
                      <div
                        style={{ fontSize: 11, color: "#9CA3AF", marginTop: 2 }}
                      >
                        {notif.time}
                      </div>
                    </div>
                    <button
                      onClick={() => onDismiss(i)}
                      style={{
                        border: "none",
                        background: "transparent",
                        cursor: "pointer",
                        color: "#9CA3AF",
                        fontSize: 16,
                        padding: "0 0 0 8px",
                        lineHeight: 1,
                      }}
                    >
                      ✕
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          <div
            style={{
              padding: "10px 18px",
              borderTop: "1px solid #F3F4F6",
              background: "#F9FAFB",
              fontSize: 11,
              color: "#9CA3AF",
              textAlign: "center",
            }}
          >
            Powered by PropIQ Collateral Health Monitor v3.0
          </div>
        </div>
      )}
    </div>
  );
}
