// PropIQ PropertyForm Component
import React from 'react';
import { PROP_TYPES } from '../utils/api';
const field = {
  label: {
    fontSize: 11, fontWeight: 600, color: '#5F5E5A', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 5, display: 'block'
  },
  input: {
    width: '100%', padding: '9px 11px', border: '1px solid rgba(44,44,42,0.15)',
    borderRadius: 8, fontSize: 13, color: '#2C2C2A', background: '#fff',
    outline: 'none', transition: 'border-color 0.15s', fontFamily: 'Inter, sans-serif'
  },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 },
  full: { marginBottom: 14 },
  toggle: { display: 'flex', gap: 8 },
  toggleBtn: (active) => ({
    flex: 1, padding: '8px 0', border: `1.5px solid ${active ? '#534AB7' : 'rgba(44,44,42,0.15)'}`,
    borderRadius: 8, background: active ? '#EEEDFE' : '#fff',
    color: active ? '#3C3489' : '#5F5E5A', fontWeight: active ? 600 : 400,
    fontSize: 12, cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'Inter, sans-serif',
  }),
};

export default function PropertyForm({ form, onChange, onSubmit, loading, cityLocalities = [] }) {
  const set = (k, v) => onChange({ ...form, [k]: v });

  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit(); }}
      style={{ padding: '20px 20px 8px', overflowY: 'auto', flex: 1 }}>

      {/* Locality */}
      <div style={field.full}>
        <label style={field.label}>Locality *</label>
        <select value={form.locality || ''} onChange={e => set('locality', e.target.value)}
          style={field.input} required>
          <option value="">Select locality...</option>
          {cityLocalities.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
      </div>

      {/* Property Type */}
      <div style={field.full}>
        <label style={field.label}>Property Type *</label>
        <select value={form.prop_type || ''} onChange={e => set('prop_type', e.target.value)}
          style={field.input} required>
          <option value="">Select type...</option>
          {PROP_TYPES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
        </select>
      </div>

      {/* Size + Age */}
      <div style={field.row}>
        <div>
          <label style={field.label}>Size (sqft) *</label>
          <input type="number" min="100" max="50000" placeholder="e.g. 850"
            value={form.size_sqft || ''} onChange={e => set('size_sqft', parseFloat(e.target.value))}
            style={field.input} required />
        </div>
        <div>
          <label style={field.label}>Age (years) *</label>
          <input type="number" min="0" max="80" placeholder="e.g. 8"
            value={form.age_years !== undefined ? form.age_years : ''}
            onChange={e => set('age_years', parseFloat(e.target.value))}
            style={field.input} required />
        </div>
      </div>

      {/* Floor + Rental Yield */}
      <div style={field.row}>
        <div>
          <label style={field.label}>Floor Number</label>
          <input type="number" min="0" max="50" placeholder="e.g. 3"
            value={form.floor_num !== undefined ? form.floor_num : ''}
            onChange={e => set('floor_num', parseInt(e.target.value))}
            style={field.input} />
        </div>
        <div>
          <label style={field.label}>Rental Yield %</label>
          <input type="number" min="0" max="15" step="0.1" placeholder="0.0"
            value={form.rental_yield_pct || ''}
            onChange={e => set('rental_yield_pct', parseFloat(e.target.value) || 0)}
            style={field.input} />
        </div>
      </div>

      {/* Freehold toggle */}
      <div style={field.full}>
        <label style={field.label}>Title Type</label>
        <div style={field.toggle}>
          <button type="button" style={field.toggleBtn(form.is_freehold !== 0)}
            onClick={() => set('is_freehold', 1)}>Freehold</button>
          <button type="button" style={field.toggleBtn(form.is_freehold === 0)}
            onClick={() => set('is_freehold', 0)}>Leasehold</button>
        </div>
      </div>

      {/* RERA toggle */}
      <div style={field.full}>
        <label style={field.label}>RERA Registered</label>
        <div style={field.toggle}>
          <button type="button" style={field.toggleBtn(form.is_rera_registered !== 0)}
            onClick={() => set('is_rera_registered', 1)}>Yes</button>
          <button type="button" style={field.toggleBtn(form.is_rera_registered === 0)}
            onClick={() => set('is_rera_registered', 0)}>No</button>
        </div>
      </div>

      {/* Occupancy */}
      <div style={{ ...field.full, marginBottom: 20 }}>
        <label style={field.label}>Occupancy</label>
        <div style={field.toggle}>
          {['self_occupied', 'rented', 'vacant'].map(o => (
            <button key={o} type="button"
              style={field.toggleBtn(form.occupancy === o)}
              onClick={() => set('occupancy', o)}>
              {o.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button type="submit" disabled={loading}
        style={{
          width: '100%', padding: '12px', background: loading ? '#AFA9EC' : '#534AB7',
          color: '#fff', border: 'none', borderRadius: 10, fontSize: 14,
          fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          letterSpacing: '0.02em', fontFamily: 'Inter, sans-serif',
          transition: 'background 0.2s',
        }}>
        {loading ? 'Assessing...' : '⚡ Run Assessment'}
      </button>
    </form>
  );
}