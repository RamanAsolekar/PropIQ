// PropIQ PropertyMap Component
import React, { useEffect, useRef } from 'react';

const PUNE_COORDS = {
  'Koregaon Park':  [18.5362, 73.8938],
  'Baner':          [18.5590, 73.7868],
  'Kothrud':        [18.5074, 73.8077],
  'Wakad':          [18.5975, 73.7614],
  'Hinjewadi':      [18.5912, 73.7380],
  'Hadapsar':       [18.5018, 73.9260],
  'Wagholi':        [18.5617, 73.9757],
  'Talegaon':       [18.7332, 73.6723],
  'Chakan':         [18.7601, 73.8637],
  'Shivajinagar':   [18.5308, 73.8474],
  'Aundh':          [18.5578, 73.8073],
  'Viman Nagar':    [18.5679, 73.9143],
  'Pimpri':         [18.6279, 73.7997],
  'Chinchwad':      [18.6436, 73.7983],
  'Katraj':         [18.4601, 73.8669],
  'Ambegaon':       [18.4489, 73.8526],
};

export default function PropertyMap({ locality, result }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);

  const coords = (locality && PUNE_COORDS[locality])
    ? PUNE_COORDS[locality]
    : (result?.enrichment?.geo?.lat
        ? [result.enrichment.geo.lat, result.enrichment.geo.lon]
        : [18.5204, 73.8567]); // Pune center

  useEffect(() => {
    if (!mapRef.current || !window.L) return;

    // Init map once
    if (!mapInstanceRef.current) {
      mapInstanceRef.current = window.L.map(mapRef.current, {
        center: coords, zoom: 14, zoomControl: true,
      });
      window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
      }).addTo(mapInstanceRef.current);
    }

    // Update marker
    if (markerRef.current) markerRef.current.remove();

    const popupContent = result
      ? `<div style="font-family:Inter,sans-serif;min-width:160px">
          <div style="font-weight:700;font-size:13px;margin-bottom:4px">${locality}</div>
          <div style="font-size:12px;color:#534AB7;font-weight:600">
            ₹${(result.market_value_mid/1e5).toFixed(1)}L (mid est.)</div>
          <div style="font-size:11px;color:#888780;margin-top:2px">
            RPI: ${result.resale_potential_index} · Confidence: ${Math.round(result.confidence_score * 100)}%
          </div>
        </div>`
      : `<b style="font-family:Inter,sans-serif">${locality || 'Pune'}</b>`;

    const icon = window.L.divIcon({
      className: '',
      html: `<div style="width:32px;height:32px;background:#534AB7;border-radius:50% 50% 50% 0;
               transform:rotate(-45deg);border:3px solid #fff;
               box-shadow:0 2px 8px rgba(83,74,183,0.5)"></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });

    markerRef.current = window.L.marker(coords, { icon })
      .addTo(mapInstanceRef.current)
      .bindPopup(popupContent);

    mapInstanceRef.current.setView(coords, 14);

    if (result) markerRef.current.openPopup();
  }, [locality, result]);

  return (
    <div style={{ padding: '0 20px 16px' }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: '#5F5E5A',
        textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
        Property Location
      </div>
      <div ref={mapRef} style={{ height: 180, borderRadius: 10,
        border: '1px solid rgba(44,44,42,0.12)', overflow: 'hidden' }} />
      {coords && (
        <div style={{ fontSize: 10, color: '#888780', marginTop: 4, textAlign: 'right' }}>
          {coords[0].toFixed(4)}, {coords[1].toFixed(4)}
        </div>
      )}
    </div>
  );
}