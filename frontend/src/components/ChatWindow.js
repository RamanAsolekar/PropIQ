// PropIQ ChatWindow Component
import React, { useState, useRef, useEffect } from 'react';
import { parsePropertyInput, generateBotResponse } from '../utils/chatParser';

const QUICK_PROMPTS = [
  '2BHK in Baner, 850 sqft, 8 years old',
  '3BHK apartment in Kothrud, 1200 sqft, 5 years',
  'Villa in Koregaon Park, 3000 sqft, 12 years',
  'Shop in Hadapsar, 400 sqft, 6 years old',
];

export default function ChatWindow({ form, onFormUpdate, onAssess, onPDF, loading }) {
  const [messages, setMessages] = useState([
    {
      id: 1, role: 'bot',
      text: "Hi! I'm **PropIQ** 👋\n\nTell me about the property you want to assess. Try:\n\n*\"2BHK in Baner, 850 sqft, 8 years old, 5th floor\"*\n\nOr use the quick prompts below.",
    },
  ]);
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (role, text, extra = {}) => {
    setMessages(prev => [...prev, { id: Date.now(), role, text, ...extra }]);
  };

  const handleSend = (text) => {
    const msg = text || input.trim();
    if (!msg) return;
    setInput('');
    addMessage('user', msg);

    // Parse property data from natural language
    const { extracted, missing } = parsePropertyInput(msg);
    const updatedForm = { ...form, ...extracted };
    if (Object.keys(extracted).length > 0) onFormUpdate(updatedForm);

    // Generate bot response
    setTimeout(() => {
      const { text: botText, action } = generateBotResponse(msg, updatedForm, missing);

      if (action === 'ASSESS') {
        addMessage('bot', botText);
        setTimeout(() => onAssess(), 300);
        return;
      }
      if (action === 'PDF') {
        addMessage('bot', botText);
        setTimeout(() => onPDF(), 300);
        return;
      }

      // Show what was extracted
      if (Object.keys(extracted).length > 0) {
        const extracted_summary = Object.entries(extracted)
          .filter(([k]) => ['locality','prop_type','size_sqft','age_years','floor_num'].includes(k))
          .map(([k, v]) => {
            const labels = { locality: '📍 Locality', prop_type: '🏠 Type',
              size_sqft: '📐 Size', age_years: '📅 Age', floor_num: '🔢 Floor' };
            const display = k === 'prop_type' ? v.replace(/_/g,' ').toUpperCase()
              : k === 'size_sqft' ? `${v} sqft`
              : k === 'age_years' ? `${v} years`
              : k === 'floor_num' ? `Floor ${v}`
              : v;
            return `${labels[k] || k}: **${display}**`;
          }).join('\n');

        const fullText = extracted_summary
          ? `Got it! Extracted:\n${extracted_summary}\n\n${missing.length > 0
            ? `Still need: ${missing.join(', ')}`
            : "Form is complete — click **Run Assessment** or say *\"assess now\"*!"}`
          : botText;
        addMessage('bot', fullText);
      } else {
        addMessage('bot', botText);
      }
    }, 400);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  // Render markdown-lite (bold + italic + newlines)
  const renderText = (text) => {
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**'))
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      if (part.startsWith('*') && part.endsWith('*'))
        return <em key={i}>{part.slice(1, -1)}</em>;
      return part.split('\n').map((line, j) =>
        j === 0 ? line : [<br key={j} />, line]
      );
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 16px 8px', display: 'flex',
                    flexDirection: 'column', gap: 12 }}>
        {messages.map(msg => (
          <div key={msg.id} style={{
            display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            alignItems: 'flex-end', gap: 8,
          }}>
            {msg.role === 'bot' && (
              <div style={{ width: 28, height: 28, borderRadius: '50%',
                background: 'linear-gradient(135deg, #534AB7, #1D9E75)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, flexShrink: 0, color: '#fff', fontWeight: 700 }}>P</div>
            )}
            <div style={{
              maxWidth: '78%', padding: '10px 14px',
              background: msg.role === 'user' ? '#534AB7' : '#fff',
              color: msg.role === 'user' ? '#fff' : '#2C2C2A',
              borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
              fontSize: 13, lineHeight: 1.6,
              boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
              border: msg.role === 'bot' ? '1px solid rgba(44,44,42,0.08)' : 'none',
            }}>
              {renderText(msg.text)}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 28, height: 28, borderRadius: '50%',
              background: 'linear-gradient(135deg, #534AB7, #1D9E75)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, color: '#fff', fontWeight: 700 }}>P</div>
            <div style={{ background: '#fff', border: '1px solid rgba(44,44,42,0.08)',
              borderRadius: '16px 16px 16px 4px', padding: '12px 16px',
              display: 'flex', gap: 4, alignItems: 'center' }}>
              {[0,1,2].map(i => (
                <div key={i} style={{
                  width: 7, height: 7, borderRadius: '50%', background: '#534AB7',
                  animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      <div style={{ padding: '0 16px 8px', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {QUICK_PROMPTS.map((p, i) => (
          <button key={i} onClick={() => handleSend(p)}
            style={{
              padding: '5px 10px', background: '#EEEDFE', border: '1px solid #CECBF6',
              borderRadius: 20, fontSize: 11, color: '#3C3489', cursor: 'pointer',
              fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap',
            }}>{p.length > 30 ? p.slice(0, 28) + '…' : p}</button>
        ))}
      </div>

      {/* Input */}
      <div style={{ padding: '8px 16px 16px', display: 'flex', gap: 8 }}>
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey} placeholder="Describe the property..."
          style={{
            flex: 1, padding: '10px 14px', border: '1.5px solid rgba(44,44,42,0.15)',
            borderRadius: 24, fontSize: 13, outline: 'none', fontFamily: 'Inter, sans-serif',
            background: '#fff',
          }} />
        <button onClick={() => handleSend()} disabled={!input.trim() || loading}
          style={{
            width: 40, height: 40, borderRadius: '50%',
            background: input.trim() ? '#534AB7' : '#D3D1C7',
            border: 'none', cursor: input.trim() ? 'pointer' : 'default',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 16, transition: 'background 0.2s',
            flexShrink: 0,
          }}>→</button>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
}