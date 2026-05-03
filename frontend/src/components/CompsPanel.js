// PropIQ CompsPanel — Comparable Properties
import React from "react";
import { formatINR } from "../utils/api";

const SIMILARITY_COLORS = {
  "Very similar": { bg: "#E1F5EE", text: "#085041", border: "#9FE1CB" },
  Similar: { bg: "#EEEDFE", text: "#3C3489", border: "#CECBF6" },
  Comparable: { bg: "#F1EFE8", text: "#444441", border: "#D3D1C7" },
};

export default function CompsPanel({ comps, compStats, locality }) {
  if (!comps || comps.length === 0) {
    return (
      <div
        style={{
          padding: 16,
          textAlign: "center",
          color: "#888780",
          fontSize: 13,
        }}
      >
        No comparable properties found for this locality.
      </div>
    );
  }

  return (
    <div style={{ padding: "0 0 8px" }}>
      {/* Market Stats Header */}
      {compStats && compStats.count > 0 && (
        <div
          style={{
            background: "#EEEDFE",
            border: "1px solid #CECBF6",
            borderRadius: 10,
            padding: "12px 16px",
            marginBottom: 14,
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: "#3C3489",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              marginBottom: 8,
            }}
          >
            {locality} Market — {compStats.count} listings analysed
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 8,
            }}
          >
            {[
              {
                label: "Avg ask",
                value: `₹${compStats.avg_price_sqft?.toLocaleString()}/sqft`,
              },
              {
                label: "Low",
                value: `₹${compStats.min_price_sqft?.toLocaleString()}/sqft`,
              },
              {
                label: "High",
                value: `₹${compStats.max_price_sqft?.toLocaleString()}/sqft`,
              },
            ].map((m) => (
              <div key={m.label} style={{ textAlign: "center" }}>
                <div
                  style={{ fontSize: 13, fontWeight: 700, color: "#2C2C2A" }}
                >
                  {m.value}
                </div>
                <div style={{ fontSize: 10, color: "#5F5E5A" }}>{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comp Cards */}
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: "#888780",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginBottom: 8,
          paddingLeft: 2,
        }}
      >
        {comps.length} Comparable Properties
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {comps.map((comp, i) => {
          const sc =
            SIMILARITY_COLORS[comp.similarity_label] ||
            SIMILARITY_COLORS["Comparable"];
          return (
            <div
              key={i}
              style={{
                background: "#fff",
                border: "1px solid rgba(44,44,42,0.10)",
                borderRadius: 10,
                padding: "11px 14px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: 6,
                }}
              >
                <div>
                  <div
                    style={{ fontSize: 13, fontWeight: 500, color: "#2C2C2A" }}
                  >
                    {comp.address_hint}
                  </div>
                  <div style={{ fontSize: 11, color: "#888780", marginTop: 1 }}>
                    {comp.locality} · Listed {comp.listing_date}
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    padding: "3px 8px",
                    borderRadius: 20,
                    background: sc.bg,
                    color: sc.text,
                    border: `1px solid ${sc.border}`,
                    whiteSpace: "nowrap",
                  }}
                >
                  {comp.similarity_label}
                </span>
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr 1fr",
                  gap: 4,
                }}
              >
                {[
                  {
                    label: "Size",
                    value: `${comp.size_sqft?.toLocaleString()} sqft`,
                  },
                  { label: "Age", value: `${comp.age_years?.toFixed(0)} yrs` },
                  {
                    label: "₹/sqft",
                    value: `₹${comp.price_per_sqft?.toLocaleString()}`,
                  },
                  { label: "Total", value: formatINR(comp.total_price) },
                ].map((d) => (
                  <div
                    key={d.label}
                    style={{
                      background: "#F7F6F2",
                      borderRadius: 6,
                      padding: "5px 7px",
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        color: "#2C2C2A",
                      }}
                    >
                      {d.value}
                    </div>
                    <div
                      style={{ fontSize: 9, color: "#888780", marginTop: 1 }}
                    >
                      {d.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
