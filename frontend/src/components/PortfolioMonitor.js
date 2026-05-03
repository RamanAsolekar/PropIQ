// PropIQ Portfolio Monitor — Collateral Health Monitor Dashboard
import React, { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000";
const API_KEY = "propiq-demo-2026";

const RISK_CONFIG = {
  red: {
    color: "#DC2626",
    bg: "#FEF2F2",
    label: "🔴 Breach Risk",
    border: "#FCA5A5",
  },
  amber: {
    color: "#D97706",
    bg: "#FFFBEB",
    label: "🟡 Warning",
    border: "#FCD34D",
  },
  green: {
    color: "#059669",
    bg: "#ECFDF5",
    label: "🟢 Healthy",
    border: "#6EE7B7",
  },
};

function fmt(val) {
  if (!val && val !== 0) return "—";
  if (val >= 1e7) return `₹${(val / 1e7).toFixed(2)} Cr`;
  if (val >= 1e5) return `₹${(val / 1e5).toFixed(1)} L`;
  return `₹${val.toLocaleString("en-IN")}`;
}

function AddLoanModal({ onClose, onAdded }) {
  const [form, setForm] = useState({
    loan_id: "",
    borrower_name: "",
    borrower_email: "",
    locality: "",
    prop_type: "2bhk_apartment",
    size_sqft: "",
    age_years: "",
    floor_num: 3,
    loan_amount: "",
    original_value: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/v1/loans`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
        body: JSON.stringify({
          ...form,
          size_sqft: parseFloat(form.size_sqft),
          age_years: parseFloat(form.age_years),
          loan_amount: parseFloat(form.loan_amount),
          original_value: parseFloat(form.original_value),
          disbursed_on: new Date().toISOString(),
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed");
      onAdded();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const inp = {
    style: {
      width: "100%",
      padding: "8px 10px",
      border: "1px solid #E5E7EB",
      borderRadius: 6,
      fontSize: 13,
      outline: "none",
      boxSizing: "border-box",
      fontFamily: "Inter, sans-serif",
    },
  };
  const lbl = {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: "#6B7280",
      textTransform: "uppercase",
      letterSpacing: "0.05em",
      marginBottom: 4,
      display: "block",
    },
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 16,
          padding: 32,
          width: 560,
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 24,
          }}
        >
          <h3
            style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#111" }}
          >
            Add Loan to Monitor
          </h3>
          <button
            onClick={onClose}
            style={{
              border: "none",
              background: "none",
              fontSize: 20,
              cursor: "pointer",
              color: "#9CA3AF",
            }}
          >
            ✕
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}
          >
            {[
              ["loan_id", "Loan ID", "text", "PF-2001"],
              ["borrower_name", "Borrower Name", "text", "Ravi Kumar"],
              ["borrower_email", "Borrower Email", "email", "ravi@example.com"],
              ["locality", "Locality", "text", "Baner"],
              ["size_sqft", "Size (sqft)", "number", "850"],
              ["age_years", "Age (years)", "number", "5"],
              ["loan_amount", "Loan Amount (₹)", "number", "7000000"],
              ["original_value", "Original Value (₹)", "number", "10800000"],
            ].map(([key, label, type, ph]) => (
              <div key={key}>
                <label {...lbl}>{label}</label>
                <input
                  {...inp}
                  type={type}
                  placeholder={ph}
                  value={form[key]}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, [key]: e.target.value }))
                  }
                  required
                />
              </div>
            ))}
            <div>
              <label {...lbl}>Property Type</label>
              <select
                {...inp}
                value={form.prop_type}
                onChange={(e) =>
                  setForm((f) => ({ ...f, prop_type: e.target.value }))
                }
              >
                {[
                  "1bhk_apartment",
                  "2bhk_apartment",
                  "3bhk_apartment",
                  "4bhk_apartment",
                  "villa",
                  "shop",
                  "office",
                  "plot",
                ].map((t) => (
                  <option key={t} value={t}>
                    {t.replace(/_/g, " ").toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {error && (
            <div style={{ marginTop: 12, color: "#DC2626", fontSize: 13 }}>
              ⚠ {error}
            </div>
          )}
          <div
            style={{
              marginTop: 24,
              display: "flex",
              gap: 12,
              justifyContent: "flex-end",
            }}
          >
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: "10px 20px",
                border: "1px solid #E5E7EB",
                borderRadius: 8,
                background: "#fff",
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              style={{
                padding: "10px 20px",
                border: "none",
                borderRadius: 8,
                background: "#534AB7",
                color: "#fff",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              {saving ? "Adding…" : "Add Loan"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PortfolioMonitor({ notifications, setNotifications }) {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [lastRun, setLastRun] = useState(null);
  const [showAddLoan, setShowAddLoan] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState({
    red: 0,
    amber: 0,
    green: 0,
    checked: 0,
  });
  const [simulating, setSimulating] = useState(false);
  const [stressResult, setStressResult] = useState(null);

  const fetchLoans = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/loans`, {
        headers: { "X-API-Key": API_KEY },
      });
      const data = await res.json();
      const loanList = data.loans || [];
      setLoans(loanList);
      const red = loanList.filter(
        (l) => l.latest_snapshot?.risk_level === "red",
      ).length;
      const amber = loanList.filter(
        (l) => l.latest_snapshot?.risk_level === "amber",
      ).length;
      const green = loanList.filter(
        (l) => l.latest_snapshot?.risk_level === "green",
      ).length;
      setSummary({
        red,
        amber,
        green,
        checked: loanList.filter((l) => l.latest_snapshot).length,
      });

      // Push notifications for red/amber
      const alerts = loanList.filter((l) =>
        ["red", "amber"].includes(l.latest_snapshot?.risk_level),
      );
      if (alerts.length > 0) {
        setNotifications((prev) => {
          const existing = new Set(prev.map((n) => n.loan_id));
          const newAlerts = alerts
            .filter((l) => !existing.has(l.loan_id))
            .map((l) => ({
              loan_id: l.loan_id,
              risk_level: l.latest_snapshot.risk_level,
              locality: l.locality,
              ltv: l.latest_snapshot.current_ltv,
              message: `Loan ${l.loan_id} (${l.locality}) — LTV ${l.latest_snapshot.current_ltv.toFixed(1)}%`,
              time: new Date().toLocaleTimeString(),
            }));
          return [...prev, ...newAlerts];
        });
      }
    } catch (err) {
      console.error("Failed to fetch loans:", err);
    } finally {
      setLoading(false);
    }
  }, [setNotifications]);

  const runHealthCheck = async () => {
    setChecking(true);
    try {
      const res = await fetch(`${API}/api/v1/loans/health-check`, {
        method: "POST",
        headers: { "X-API-Key": API_KEY },
      });
      const data = await res.json();
      setLastRun(new Date().toLocaleTimeString());
      await fetchLoans();
      return data;
    } catch (err) {
      console.error("Health check failed:", err);
    } finally {
      setChecking(false);
    }
  };

  const runStressTest = async () => {
    setSimulating(true);
    setStressResult(null);
    try {
      const res = await fetch(`${API}/api/v1/loans/stress-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
        body: JSON.stringify({ shock_pct: -20.0 }), // -20% property value shock
      });
      const data = await res.json();
      setStressResult(data);
    } catch (err) {
      console.error("Stress test failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  const fetchHistory = async (loan_id) => {
    try {
      const res = await fetch(`${API}/api/v1/loans/${loan_id}/history`, {
        headers: { "X-API-Key": API_KEY },
      });
      const data = await res.json();
      setHistory(data.history || []);
    } catch (err) {
      setHistory([]);
    }
  };

  useEffect(() => {
    fetchLoans();
  }, [fetchLoans]);

  const selectLoan = (loan) => {
    setSelectedLoan(loan);
    fetchHistory(loan.loan_id);
  };

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, sans-serif",
        background: "#F9FAFB",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: "#0D0E15",
          padding: "16px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <div>
          <div
            style={{
              color: "#7C6FD8",
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
            }}
          >
            PropIQ · Collateral Health Monitor
          </div>
          <div
            style={{
              color: "#fff",
              fontSize: 18,
              fontWeight: 700,
              marginTop: 2,
            }}
          >
            Portfolio Risk Dashboard
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {lastRun && (
            <span style={{ color: "#6B7280", fontSize: 12 }}>
              Last run: {lastRun}
            </span>
          )}
          <button
            onClick={() => setShowAddLoan(true)}
            style={{
              padding: "8px 16px",
              border: "1px solid #374151",
              borderRadius: 8,
              background: "transparent",
              color: "#D1D5DB",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            + Add Loan
          </button>
          <button
            onClick={runHealthCheck}
            disabled={checking || simulating}
            style={{
              padding: "8px 20px",
              border: "none",
              borderRadius: 8,
              background: checking ? "#374151" : "#534AB7",
              color: "#fff",
              cursor: checking ? "not-allowed" : "pointer",
              fontSize: 13,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            {checking ? "⟳ Checking..." : "▶ Run Health Check"}
          </button>
          <button
            onClick={runStressTest}
            disabled={checking || simulating}
            style={{
              padding: "8px 20px",
              border: "1px solid #DC2626",
              borderRadius: 8,
              background: simulating ? "#7F1D1D" : "#FEF2F2",
              color: simulating ? "#FCA5A5" : "#DC2626",
              cursor: simulating ? "not-allowed" : "pointer",
              fontSize: 13,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            {simulating ? "⚡ Simulating Shock..." : "⚡ Black Swan Simulator"}
          </button>
        </div>
      </div>

      {/* Summary Bar */}
      <div
        style={{
          background: "#1A1B26",
          padding: "12px 24px",
          display: "flex",
          gap: 32,
          flexShrink: 0,
        }}
      >
        {[
          { label: "Total Loans", value: loans.length, color: "#9CA3AF" },
          { label: "🟢 Healthy", value: summary.green, color: "#059669" },
          { label: "🟡 Warning", value: summary.amber, color: "#D97706" },
          { label: "🔴 Breach Risk", value: summary.red, color: "#DC2626" },
        ].map(({ label, value, color }) => (
          <div key={label}>
            <div
              style={{
                fontSize: 11,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              {label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Stress Test Results Modal */}
      {stressResult && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.7)",
            zIndex: 2000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 16,
              padding: 32,
              width: 800,
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderBottom: "1px solid #E5E7EB",
                paddingBottom: 16,
                marginBottom: 24,
              }}
            >
              <div>
                <h3
                  style={{
                    margin: 0,
                    fontSize: 22,
                    fontWeight: 800,
                    color: "#DC2626",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  ⚡ Market Shock Simulation Results
                </h3>
                <div style={{ fontSize: 14, color: "#6B7280", marginTop: 4 }}>
                  Applied Shock: {stressResult.shock_applied_pct}% property
                  value drop.
                </div>
              </div>
              <button
                onClick={() => setStressResult(null)}
                style={{
                  border: "none",
                  background: "#F3F4F6",
                  borderRadius: 8,
                  width: 32,
                  height: 32,
                  fontSize: 18,
                  cursor: "pointer",
                  color: "#4B5563",
                }}
              >
                ✕
              </button>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: 16,
                marginBottom: 24,
              }}
            >
              <div
                style={{
                  background: "#F9FAFB",
                  padding: 16,
                  borderRadius: 12,
                  border: "1px solid #E5E7EB",
                }}
              >
                <div
                  style={{
                    fontSize: 12,
                    color: "#6B7280",
                    textTransform: "uppercase",
                    fontWeight: 600,
                  }}
                >
                  Loans Checked
                </div>
                <div style={{ fontSize: 24, fontWeight: 700, color: "#111" }}>
                  {stressResult.checked}
                </div>
              </div>
              <div
                style={{
                  background: "#FFFBEB",
                  padding: 16,
                  borderRadius: 12,
                  border: "1px solid #FCD34D",
                }}
              >
                <div
                  style={{
                    fontSize: 12,
                    color: "#D97706",
                    textTransform: "uppercase",
                    fontWeight: 600,
                  }}
                >
                  Red Flags Triggered
                </div>
                <div
                  style={{ fontSize: 24, fontWeight: 700, color: "#D97706" }}
                >
                  {stressResult.red_count}
                </div>
              </div>
              <div
                style={{
                  background: "#FEF2F2",
                  padding: 16,
                  borderRadius: 12,
                  border: "1px solid #FCA5A5",
                }}
              >
                <div
                  style={{
                    fontSize: 12,
                    color: "#DC2626",
                    textTransform: "uppercase",
                    fontWeight: 600,
                  }}
                >
                  Loans Underwater (&gt;100% LTV)
                </div>
                <div
                  style={{ fontSize: 24, fontWeight: 700, color: "#DC2626" }}
                >
                  {stressResult.underwater_count}
                </div>
              </div>
            </div>

            <h4 style={{ margin: "0 0 16px 0", fontSize: 16, color: "#111" }}>
              Underwater Loans & Risk Escalations
            </h4>
            {stressResult.underwater_count === 0 ? (
              <div
                style={{
                  padding: 24,
                  background: "#ECFDF5",
                  borderRadius: 8,
                  color: "#059669",
                  textAlign: "center",
                  fontWeight: 500,
                }}
              >
                No loans went underwater during this simulation. Portfolio is
                resilient.
              </div>
            ) : (
              <div
                style={{ display: "flex", flexDirection: "column", gap: 16 }}
              >
                {stressResult.results
                  .filter((r) => r.is_underwater)
                  .map((r) => (
                    <div
                      key={r.loan_id}
                      style={{
                        border: "1px solid #E5E7EB",
                        borderRadius: 12,
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          background: "#F9FAFB",
                          padding: "12px 16px",
                          borderBottom: "1px solid #E5E7EB",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <div style={{ fontWeight: 700, color: "#111" }}>
                          {r.loan_id} — {r.borrower_name}
                        </div>
                        <div
                          style={{
                            background: "#FEF2F2",
                            color: "#DC2626",
                            padding: "4px 10px",
                            borderRadius: 999,
                            fontSize: 12,
                            fontWeight: 700,
                          }}
                        >
                          LTV: {(r.stressed_ltv * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div style={{ padding: "16px" }}>
                        <div
                          style={{
                            fontSize: 13,
                            color: "#4B5563",
                            marginBottom: 12,
                          }}
                        >
                          <strong>Stressed Value:</strong>{" "}
                          {fmt(r.stressed_value)} (Down from {fmt(r.base_value)}
                          )<br />
                          <strong>Loan Amount:</strong> {fmt(r.loan_amount)}
                        </div>
                        {r.risk_escalation_memo ? (
                          <div
                            style={{
                              background: "#F3F4F6",
                              padding: 16,
                              borderRadius: 8,
                              fontSize: 13,
                              color: "#111",
                              fontFamily: "monospace",
                              whiteSpace: "pre-wrap",
                              border: "1px solid #D1D5DB",
                            }}
                          >
                            <div
                              style={{
                                fontSize: 11,
                                color: "#6B7280",
                                textTransform: "uppercase",
                                marginBottom: 8,
                                fontWeight: 700,
                              }}
                            >
                              Generated Internal Risk Alert (LLM)
                            </div>
                            {r.risk_escalation_memo}
                          </div>
                        ) : (
                          <div style={{ color: "#DC2626", fontSize: 13 }}>
                            Failed to generate internal risk alert.
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Loan Table */}
        <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
          {loading ? (
            <div style={{ textAlign: "center", padding: 48, color: "#9CA3AF" }}>
              Loading portfolio…
            </div>
          ) : (
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: 13,
              }}
            >
              <thead>
                <tr style={{ background: "#F3F4F6" }}>
                  {[
                    "Loan ID",
                    "Borrower",
                    "Property",
                    "Loan Amt",
                    "Orig. Value",
                    "Curr. Value",
                    "Δ Value",
                    "LTV",
                    "Status",
                  ].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "10px 12px",
                        textAlign: "left",
                        fontSize: 11,
                        fontWeight: 700,
                        color: "#6B7280",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        borderBottom: "1px solid #E5E7EB",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loans.map((loan) => {
                  const snap = loan.latest_snapshot;
                  const rc = RISK_CONFIG[snap?.risk_level || "green"];
                  const isSelected = selectedLoan?.loan_id === loan.loan_id;
                  return (
                    <tr
                      key={loan.loan_id}
                      onClick={() => selectLoan(loan)}
                      style={{
                        background: isSelected ? "#EEF2FF" : "#fff",
                        cursor: "pointer",
                        borderBottom: "1px solid #F3F4F6",
                        transition: "background 0.15s",
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected)
                          e.currentTarget.style.background = "#F9FAFB";
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected)
                          e.currentTarget.style.background = "#fff";
                      }}
                    >
                      <td
                        style={{
                          padding: "12px",
                          fontWeight: 700,
                          color: "#534AB7",
                        }}
                      >
                        {loan.loan_id}
                      </td>
                      <td style={{ padding: "12px", color: "#374151" }}>
                        {loan.borrower_name}
                      </td>
                      <td style={{ padding: "12px", color: "#374151" }}>
                        <div style={{ fontWeight: 600 }}>{loan.locality}</div>
                        <div style={{ color: "#9CA3AF", fontSize: 11 }}>
                          {loan.prop_type.replace(/_/g, " ")}
                        </div>
                      </td>
                      <td style={{ padding: "12px", color: "#374151" }}>
                        {fmt(loan.loan_amount)}
                      </td>
                      <td style={{ padding: "12px", color: "#374151" }}>
                        {fmt(loan.original_value)}
                      </td>
                      <td style={{ padding: "12px", color: "#374151" }}>
                        {snap ? fmt(snap.current_value) : "—"}
                      </td>
                      <td
                        style={{
                          padding: "12px",
                          color: snap?.delta_pct >= 0 ? "#059669" : "#DC2626",
                          fontWeight: 600,
                        }}
                      >
                        {snap
                          ? `${snap.delta_pct >= 0 ? "+" : ""}${snap.delta_pct.toFixed(1)}%`
                          : "—"}
                      </td>
                      <td
                        style={{
                          padding: "12px",
                          fontWeight: 700,
                          color: rc.color,
                        }}
                      >
                        {snap
                          ? `${snap.current_ltv.toFixed(1)}%`
                          : `${loan.original_ltv}%`}
                      </td>
                      <td style={{ padding: "12px" }}>
                        <span
                          style={{
                            background: rc.bg,
                            color: rc.color,
                            border: `1px solid ${rc.border}`,
                            padding: "3px 10px",
                            borderRadius: 20,
                            fontSize: 11,
                            fontWeight: 700,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {snap ? rc.label : "—"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Detail Panel */}
        {selectedLoan && (
          <div
            style={{
              width: 340,
              borderLeft: "1px solid #E5E7EB",
              background: "#fff",
              overflowY: "auto",
              padding: 20,
              flexShrink: 0,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 16,
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 15, color: "#111" }}>
                {selectedLoan.loan_id}
              </div>
              <button
                onClick={() => setSelectedLoan(null)}
                style={{
                  border: "none",
                  background: "none",
                  cursor: "pointer",
                  color: "#9CA3AF",
                  fontSize: 18,
                }}
              >
                ✕
              </button>
            </div>

            {/* Alert Box */}
            {selectedLoan.latest_snapshot &&
              selectedLoan.latest_snapshot.risk_level !== "green" &&
              (() => {
                const rc = RISK_CONFIG[selectedLoan.latest_snapshot.risk_level];
                return (
                  <div
                    style={{
                      background: rc.bg,
                      border: `1px solid ${rc.border}`,
                      borderRadius: 10,
                      padding: 14,
                      marginBottom: 16,
                    }}
                  >
                    <div
                      style={{
                        fontWeight: 700,
                        color: rc.color,
                        marginBottom: 6,
                        fontSize: 13,
                      }}
                    >
                      {rc.label}
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "#374151",
                        lineHeight: 1.5,
                      }}
                    >
                      {selectedLoan.latest_snapshot.risk_level === "red"
                        ? "LTV exceeds 80% threshold. Request additional collateral or partial repayment within 7 days."
                        : "LTV has crossed 70% warning threshold. Review borrower repayment capacity."}
                    </div>
                  </div>
                );
              })()}

            {/* Metrics */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 10,
                marginBottom: 16,
              }}
            >
              {[
                ["Borrower", selectedLoan.borrower_name],
                ["Locality", selectedLoan.locality],
                ["Property", selectedLoan.prop_type.replace(/_/g, " ")],
                ["Size", `${selectedLoan.size_sqft} sqft`],
                ["Loan Amount", fmt(selectedLoan.loan_amount)],
                ["Original Value", fmt(selectedLoan.original_value)],
                ...(selectedLoan.latest_snapshot
                  ? [
                      [
                        "Current Value",
                        fmt(selectedLoan.latest_snapshot.current_value),
                      ],
                      [
                        "Current LTV",
                        `${selectedLoan.latest_snapshot.current_ltv.toFixed(1)}%`,
                      ],
                    ]
                  : []),
              ].map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    background: "#F9FAFB",
                    borderRadius: 8,
                    padding: "10px 12px",
                  }}
                >
                  <div
                    style={{
                      fontSize: 10,
                      color: "#9CA3AF",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    {k}
                  </div>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: "#111",
                      marginTop: 2,
                    }}
                  >
                    {v}
                  </div>
                </div>
              ))}
            </div>

            {/* History */}
            <div
              style={{
                fontWeight: 700,
                fontSize: 12,
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: 10,
              }}
            >
              Assessment History
            </div>
            {history.length === 0 ? (
              <div style={{ color: "#9CA3AF", fontSize: 12 }}>
                No history yet.
              </div>
            ) : (
              history.map((h, i) => {
                const rc = RISK_CONFIG[h.risk_level];
                return (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "8px 0",
                      borderBottom: "1px solid #F3F4F6",
                      fontSize: 12,
                    }}
                  >
                    <div>
                      <div style={{ color: "#374151", fontWeight: 600 }}>
                        {fmt(h.current_value)}
                      </div>
                      <div style={{ color: "#9CA3AF", fontSize: 11 }}>
                        {h.assessed_on
                          ? new Date(h.assessed_on).toLocaleDateString("en-IN")
                          : "—"}
                      </div>
                    </div>
                    <div
                      style={{ display: "flex", gap: 8, alignItems: "center" }}
                    >
                      <span
                        style={{
                          color: h.delta_pct >= 0 ? "#059669" : "#DC2626",
                          fontWeight: 600,
                        }}
                      >
                        {h.delta_pct >= 0 ? "+" : ""}
                        {h.delta_pct.toFixed(1)}%
                      </span>
                      <span
                        style={{
                          background: rc.bg,
                          color: rc.color,
                          border: `1px solid ${rc.border}`,
                          padding: "2px 8px",
                          borderRadius: 20,
                          fontSize: 10,
                          fontWeight: 700,
                        }}
                      >
                        {h.current_ltv.toFixed(1)}% LTV
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {showAddLoan && (
        <AddLoanModal
          onClose={() => setShowAddLoan(false)}
          onAdded={fetchLoans}
        />
      )}
    </div>
  );
}
