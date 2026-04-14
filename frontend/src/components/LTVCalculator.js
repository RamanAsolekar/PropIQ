// PropIQ LTVCalculator — Interactive LTV Calculator
import React, { useState, useEffect } from 'react';
import { formatINR } from '../utils/api';

export default function LTVCalculator({ ltvAnalysis, marketValueMid }) {
  const [loanAmount, setLoanAmount] = useState(null);

  useEffect(() => {
    if (ltvAnalysis?.max_loan_amount) {
      setLoanAmount(Math.round(ltvAnalysis.max_loan_amount / 100000) * 100000);
    }
  }, [ltvAnalysis]);

  if (!ltvAnalysis || !marketValueMid) {
    return (
      <div style={{ padding: 16, textAlign: 'center', color: '#888780', fontSize: 13 }}>
        Run an assessment to see LTV calculation.
      </div>
    );
  }

  const { recommended_ltv_pct, rbi_max_ltv_pct, pfl_internal_ltv_pct,
          max_loan_amount, rbi_rationale, pfl_rationale, ltv_zone } = ltvAnalysis;

  const currentLTV = loanAmount ? Math.round((loanAmount / marketValueMid) * 100) : recommended_ltv_pct;
  const maxLoan = Math.round(max_loan_amount);
  const minLoan = Math.round(marketValueMid * 0.1);

  const zoneColors = {
    green: { bg: '#E1F5EE', text: '#085041', border: '#9FE1CB', label: 'Within RBI limits' },
    amber: { bg: '#FAEEDA', text: '#633806', border: '#FAC775', label: 'Marginal — review needed' },
    red:   { bg: '#FCEBEB', text: '#791F1F', border: '#F09595', label: 'Exceeds recommended LTV' },
  };

  const currentZone = currentLTV > rbi_max_ltv_pct ? 'red' :
                      currentLTV > pfl_internal_ltv_pct ? 'amber' : 'green';
  const zc = zoneColors[currentZone];

  return (
    <div>
      {/* LTV Visual */}
      <div style={{ background: '#fff', border: '1px solid rgba(44,44,42,0.10)',
        borderRadius: 12, padding: '16px', marginBottom: 14 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: '#888780',
          textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
          Loan-to-Value Calculator
        </div>

        {/* LTV Bar */}
        <div style={{ position: 'relative', height: 28, background: '#F1EFE8',
          borderRadius: 14, overflow: 'hidden', marginBottom: 8 }}>
          {/* PFL limit marker */}
          <div style={{ position: 'absolute', left: `${pfl_internal_ltv_pct}%`,
            top: 0, bottom: 0, width: 2, background: '#BA7517', zIndex: 2 }} />
          {/* RBI limit marker */}
          <div style={{ position: 'absolute', left: `${rbi_max_ltv_pct}%`,
            top: 0, bottom: 0, width: 2, background: '#A32D2D', zIndex: 2 }} />
          {/* Current loan bar */}
          <div style={{
            width: `${Math.min(currentLTV, 100)}%`, height: '100%',
            background: currentZone === 'green' ? '#0F6E56' :
                        currentZone === 'amber' ? '#BA7517' : '#A32D2D',
            borderRadius: 14, transition: 'width 0.3s, background 0.3s',
          }} />
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: 12, fontSize: 10, color: '#888780', marginBottom: 14 }}>
          <span><span style={{ color: '#BA7517', fontWeight: 700 }}>|</span> PFL ({pfl_internal_ltv_pct}%)</span>
          <span><span style={{ color: '#A32D2D', fontWeight: 700 }}>|</span> RBI max ({rbi_max_ltv_pct}%)</span>
          <span style={{ marginLeft: 'auto', color: zc.text, fontWeight: 700,
            background: zc.bg, padding: '2px 8px', borderRadius: 10 }}>{zc.label}</span>
        </div>

        {/* Loan slider */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
            fontSize: 12, color: '#5F5E5A', marginBottom: 6 }}>
            <span>Loan Amount</span>
            <span style={{ fontWeight: 700, color: zc.text, fontSize: 15 }}>
              {formatINR(loanAmount)} ({currentLTV}% LTV)
            </span>
          </div>
          <input type="range" min={minLoan} max={Math.round(marketValueMid * 0.95)}
            step={100000} value={loanAmount || maxLoan}
            onChange={e => setLoanAmount(parseInt(e.target.value))}
            style={{ width: '100%' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#888780' }}>
            <span>{formatINR(minLoan)}</span>
            <span>Property: {formatINR(marketValueMid)}</span>
          </div>
        </div>

        {/* Quick buttons */}
        <div style={{ display: 'flex', gap: 6 }}>
          {[
            { label: `PFL (${pfl_internal_ltv_pct}%)`, pct: pfl_internal_ltv_pct },
            { label: `RBI Max (${rbi_max_ltv_pct}%)`, pct: rbi_max_ltv_pct },
            { label: '50% (Conservative)', pct: 50 },
          ].map(b => (
            <button key={b.label} onClick={() => setLoanAmount(Math.round(marketValueMid * b.pct / 100))}
              style={{ flex: 1, padding: '6px 4px', background: '#F1EFE8',
                border: '1px solid #D3D1C7', borderRadius: 6, fontSize: 10,
                color: '#444441', cursor: 'pointer', fontFamily: 'Inter, sans-serif' }}>
              {b.label}
            </button>
          ))}
        </div>
      </div>

      {/* Rationale cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ background: '#F7F6F2', borderRadius: 10, padding: '10px 14px' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#534AB7', marginBottom: 3 }}>
            RBI Guideline
          </div>
          <div style={{ fontSize: 12, color: '#5F5E5A' }}>{rbi_rationale}</div>
        </div>
        <div style={{ background: '#F7F6F2', borderRadius: 10, padding: '10px 14px' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#0F6E56', marginBottom: 3 }}>
            PFL Internal Assessment
          </div>
          <div style={{ fontSize: 12, color: '#5F5E5A' }}>{pfl_rationale}</div>
        </div>
        <div style={{ fontSize: 10, color: '#888780', lineHeight: 1.5, paddingLeft: 2 }}>
          {ltvAnalysis.disclaimer}
        </div>
      </div>
    </div>
  );
}