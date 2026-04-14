// PropIQ PriceTrendChart — 24-month price history
import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#fff', border: '1px solid rgba(44,44,42,0.12)',
      borderRadius: 8, padding: '8px 12px', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
      <div style={{ fontWeight: 600, marginBottom: 2 }}>{label}</div>
      <div style={{ color: '#534AB7', fontWeight: 700 }}>
        ₹{payload[0]?.value?.toLocaleString()}/sqft
      </div>
    </div>
  );
};

export default function PriceTrendChart({ locality, propType = '2bhk_apartment' }) {
  const [trend, setTrend] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!locality) return;
    setLoading(true);
    axios.get(`${BASE_URL}/api/v1/trends/${encodeURIComponent(locality)}`, {
      params: { prop_type: propType },
    }).then(r => {
      setTrend(r.data.trend);
      setSummary(r.data.summary);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [locality, propType]);

  if (loading) return (
    <div style={{ height: 180, display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: '#888780', fontSize: 12 }}>Loading trend data...</div>
  );
  if (!trend) return null;

  // Show every 3rd label to avoid clutter
  const displayData = trend.map((d, i) => ({
    ...d,
    displayLabel: i % 4 === 0 ? d.label : '',
  }));

  const change = summary?.total_change_pct || 0;
  const changeColor = change > 0 ? '#0F6E56' : change < 0 ? '#A32D2D' : '#888780';

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#2C2C2A' }}>
            24-Month Price Trend — {locality}
          </div>
          <div style={{ fontSize: 11, color: '#888780', marginTop: 2 }}>
            {trend[0]?.label} → {trend[trend.length - 1]?.label}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: changeColor }}>
            {change > 0 ? '+' : ''}{change}%
          </div>
          <div style={{ fontSize: 10, color: '#888780' }}>24-month return</div>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={displayData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#534AB7" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#534AB7" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <XAxis dataKey="displayLabel" tick={{ fontSize: 9, fill: '#888780' }}
            axisLine={false} tickLine={false} />
          <YAxis tickFormatter={v => `₹${(v/1000).toFixed(0)}k`}
            tick={{ fontSize: 9, fill: '#888780' }} axisLine={false} tickLine={false} width={42} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={trend[0]?.price_per_sqft} stroke="#D3D1C7"
            strokeDasharray="4 4" strokeWidth={0.8} />
          <Area type="monotone" dataKey="price_per_sqft"
            stroke="#534AB7" strokeWidth={2}
            fill="url(#trendGrad)" dot={false} activeDot={{ r: 4, fill: '#534AB7' }} />
        </AreaChart>
      </ResponsiveContainer>

      {/* Summary pills */}
      {summary && (
        <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
          {[
            { label: 'Start', value: `₹${summary.start_price?.toLocaleString()}/sqft` },
            { label: 'Current', value: `₹${summary.current_price?.toLocaleString()}/sqft` },
            { label: 'Last 6m', value: `${summary.last_6m_change_pct > 0 ? '+' : ''}${summary.last_6m_change_pct}%` },
            { label: 'Annualised', value: `${summary.annualized_return_pct}%/yr` },
          ].map(p => (
            <div key={p.label} style={{ background: '#F1EFE8', borderRadius: 6,
              padding: '4px 10px', fontSize: 11 }}>
              <span style={{ color: '#888780' }}>{p.label}: </span>
              <span style={{ fontWeight: 600, color: '#2C2C2A' }}>{p.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}