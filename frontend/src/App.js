// PropIQ Main App v2 — 3 cities, 7-tab dashboard, batch mode
import React, { useState, useCallback } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import ChatWindow from './components/ChatWindow';
import PropertyForm from './components/PropertyForm';
import ResultsDashboard from './components/ResultsDashboard';
import ImageUpload from './components/ImageUpload';
import PropertyMap from './components/PropertyMap';
import BatchUpload from './components/BatchUpload';
import { assessFull, assessWithImage, downloadPDF, LOCALITIES_BY_CITY } from './utils/api';
import './styles/global.css';

if (!window.L) {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
  document.head.appendChild(link);
  const script = document.createElement('script');
  script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
  document.head.appendChild(script);
}

const DEFAULT_FORM = {
  locality: '', prop_type: '', size_sqft: '', age_years: '',
  floor_num: 3, is_freehold: 1, is_rera_registered: 1,
  occupancy: 'self_occupied', rental_yield_pct: 0,
};

export default function App() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingPDF, setLoadingPDF] = useState(false);
  const [activePanel, setActivePanel] = useState('chat');
  const [selectedCity, setSelectedCity] = useState('Pune');
  const [mode, setMode] = useState('single'); // 'single' | 'batch'

  const handleAssess = useCallback(async () => {
    if (!form.locality || !form.prop_type || !form.size_sqft || form.age_years === '') {
      toast.error('Please fill in: locality, property type, size, and age');
      return;
    }
    setLoading(true);
    try {
      let data;
      if (image) {
        // Image mode — CV assessment, then fetch full data
        data = await assessWithImage(form, image);
        toast.success(`CV: ${data.cv_assessment?.condition?.toUpperCase()} detected`);
      } else {
        // Full mode — all enrichments in one call
        data = await assessFull(form);
      }
      setResult(data);
      toast.success('Assessment complete!');
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Assessment failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [form, image]);

  const handlePDF = useCallback(async () => {
    if (!form.locality) { toast.error('Run an assessment first'); return; }
    setLoadingPDF(true);
    try {
      await downloadPDF(form);
      toast.success('PDF downloaded!');
    } catch { toast.error('PDF generation failed'); }
    finally { setLoadingPDF(false); }
  }, [form]);

  const cityLocalities = LOCALITIES_BY_CITY[selectedCity] || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh',
      background: '#F7F6F2', fontFamily: 'Inter, sans-serif' }}>
      <Toaster position="top-right" toastOptions={{ duration: 3000,
        style: { fontFamily: 'Inter, sans-serif', fontSize: 13 } }} />

      {/* ── Navbar ──────────────────────────────────────────────────── */}
      <nav style={{ background: '#fff', borderBottom: '1px solid rgba(44,44,42,0.10)',
        padding: '0 20px', height: 54, display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', flexShrink: 0, zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 8,
            background: 'linear-gradient(135deg, #534AB7, #0F6E56)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 800, fontSize: 13 }}>P</div>
          <div>
            <span style={{ fontWeight: 800, fontSize: 15, color: '#2C2C2A' }}>PropIQ</span>
            <span style={{ fontSize: 11, color: '#888780', marginLeft: 8 }}>
              AI Collateral Intelligence
            </span>
          </div>
          {/* City selector */}
          <div style={{ display: 'flex', gap: 4, marginLeft: 12, background: '#F1EFE8',
            borderRadius: 8, padding: 3 }}>
            {['Pune', 'Mumbai', 'Bangalore'].map(city => (
              <button key={city} onClick={() => setSelectedCity(city)}
                style={{ padding: '4px 12px', border: 'none', borderRadius: 6,
                  background: selectedCity === city ? '#fff' : 'transparent',
                  color: selectedCity === city ? '#534AB7' : '#888780',
                  fontSize: 11, fontWeight: selectedCity === city ? 600 : 400,
                  cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                  boxShadow: selectedCity === city ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s' }}>{city}</button>
            ))}
          </div>
          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: 4, marginLeft: 8, background: '#F1EFE8',
            borderRadius: 8, padding: 3 }}>
            {[{k:'single',l:'Single'},{k:'batch',l:'Batch'}].map(m => (
              <button key={m.k} onClick={() => setMode(m.k)}
                style={{ padding: '4px 12px', border: 'none', borderRadius: 6,
                  background: mode === m.k ? '#fff' : 'transparent',
                  color: mode === m.k ? '#534AB7' : '#888780',
                  fontSize: 11, fontWeight: mode === m.k ? 600 : 400,
                  cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                  boxShadow: mode === m.k ? '0 1px 3px rgba(0,0,0,0.08)' : 'none' }}>{m.l}</button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#0F6E56' }} />
          <span style={{ fontSize: 11, color: '#5F5E5A' }}>3 cities · 39 localities · MAPE 8.3%</span>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
            style={{ fontSize: 11, color: '#534AB7', textDecoration: 'none',
              padding: '4px 10px', background: '#EEEDFE', borderRadius: 6, fontWeight: 500 }}>
            API Docs ↗
          </a>
        </div>
      </nav>

      {/* ── Main Layout ──────────────────────────────────────────────── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* ── Left Panel ───────────────────────────────────────────── */}
        <div style={{ width: 360, flexShrink: 0, display: 'flex', flexDirection: 'column',
          borderRight: '1px solid rgba(44,44,42,0.10)', background: '#fff' }}>
          {mode === 'batch' ? (
            <div style={{ flex: 1, overflowY: 'auto', paddingTop: 16 }}>
              <BatchUpload onViewProperty={setResult} />
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', borderBottom: '1px solid rgba(44,44,42,0.10)',
                padding: '0 16px', background: '#fff', flexShrink: 0 }}>
                {[{ k:'chat', l:'💬 Chat' }, { k:'form', l:'📋 Form' }].map(p => (
                  <button key={p.k} onClick={() => setActivePanel(p.k)}
                    style={{ padding: '13px 16px', background: 'none', border: 'none',
                      borderBottom: `2px solid ${activePanel === p.k ? '#534AB7' : 'transparent'}`,
                      color: activePanel === p.k ? '#534AB7' : '#888780',
                      fontSize: 13, fontWeight: activePanel === p.k ? 600 : 400,
                      cursor: 'pointer', fontFamily: 'Inter, sans-serif', marginBottom: -1 }}>
                    {p.l}
                  </button>
                ))}
              </div>
              {activePanel === 'chat' ? (
                <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                  <ChatWindow form={form} onFormUpdate={setForm}
                    onAssess={handleAssess} onPDF={handlePDF} loading={loading} />
                </div>
              ) : (
                <div style={{ flex: 1, overflowY: 'auto' }}>
                  <PropertyForm form={form} onChange={setForm}
                    onSubmit={handleAssess} loading={loading}
                    cityLocalities={cityLocalities} />
                </div>
              )}
            </>
          )}
        </div>

        {/* ── Middle Panel ─────────────────────────────────────────── */}
        {mode === 'single' && (
          <div style={{ width: 270, flexShrink: 0, display: 'flex', flexDirection: 'column',
            borderRight: '1px solid rgba(44,44,42,0.10)', background: '#FAFAF8',
            overflowY: 'auto', paddingTop: 16 }}>
            <PropertyMap locality={form.locality} result={result} city={selectedCity} />
            <ImageUpload onImageSelect={setImage} image={image} />
            {form.locality && (
              <div style={{ margin: '0 20px', background: '#fff',
                border: '1px solid rgba(44,44,42,0.10)', borderRadius: 10, padding: '12px 14px',
                marginBottom: 16 }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: '#888780',
                  textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                  Selected Property
                </div>
                {[['City', selectedCity],['Locality',form.locality],
                  ['Type',form.prop_type?.replace(/_/g,' ')],
                  ['Size',form.size_sqft ? `${form.size_sqft} sqft`:null],
                  ['Age',form.age_years !== '' ? `${form.age_years} yrs`:null],
                  ['Title',form.is_freehold ? 'Freehold':'Leasehold'],
                ].filter(([,v])=>v).map(([k,v])=>(
                  <div key={k} style={{ display:'flex',justifyContent:'space-between',
                    fontSize:12,padding:'3px 0',borderBottom:'1px solid rgba(44,44,42,0.05)'}}>
                    <span style={{color:'#888780'}}>{k}</span>
                    <span style={{fontWeight:500,color:'#2C2C2A',textTransform:'capitalize'}}>{v}</span>
                  </div>
                ))}
                {image && <div style={{ marginTop:8,fontSize:11,color:'#0F6E56',fontWeight:600,
                  textAlign:'center',background:'#E1F5EE',borderRadius:6,padding:'4px'}}>
                  📷 CV Analysis Active</div>}
              </div>
            )}
          </div>
        )}

        {/* ── Right Panel ──────────────────────────────────────────── */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {result ? (
            <ResultsDashboard result={result} onDownloadPDF={handlePDF} loadingPDF={loadingPDF} />
          ) : mode === 'single' ? (
            <div style={{ flex:1,display:'flex',flexDirection:'column',alignItems:'center',
              justifyContent:'center',padding:40,textAlign:'center'}}>
              <div style={{width:72,height:72,borderRadius:20,marginBottom:20,
                background:'linear-gradient(135deg,#EEEDFE,#E1F5EE)',
                display:'flex',alignItems:'center',justifyContent:'center',fontSize:32}}>🏠</div>
              <div style={{fontSize:20,fontWeight:700,color:'#2C2C2A',marginBottom:8}}>
                AI Collateral Assessment
              </div>
              <div style={{fontSize:13,color:'#888780',maxWidth:360,lineHeight:1.7,marginBottom:24}}>
                Enter property details via chat or form to get a complete valuation — covering
                Pune, Mumbai, and Bangalore with comparable sales, price trends, LTV, and more.
              </div>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,width:'100%',maxWidth:400}}>
                {[['⚡','Sub-90 second assessment'],['📊','P10/P50/P90 value range'],
                  ['🔍','SHAP explainability'],['📋','RBI-ready PDF report'],
                  ['📷','CV condition scoring'],['🏘','Comparable sales'],
                  ['📈','24-month price trend'],['💰','LTV calculation'],
                ].map(([icon,text])=>(
                  <div key={text} style={{background:'#fff',border:'1px solid rgba(44,44,42,0.08)',
                    borderRadius:10,padding:'11px 14px',display:'flex',alignItems:'center',
                    gap:8,fontSize:12,color:'#5F5E5A'}}>
                    <span style={{fontSize:16}}>{icon}</span>{text}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}