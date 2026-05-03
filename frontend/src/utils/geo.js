// PropIQ Geo Utilities — geocode + nearest-locality resolver

/** Haversine distance in km between two [lat,lon] pairs */
function haversine([lat1, lon1], [lat2, lon2]) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/** All known locality coordinates (same as PropertyMap) */
export const LOCALITY_COORDS = {
  // Pune
  "Koregaon Park": [18.5362, 73.8938],
  Baner: [18.559, 73.7868],
  Kothrud: [18.5074, 73.8077],
  Wakad: [18.5975, 73.7614],
  Hinjewadi: [18.5912, 73.738],
  Hadapsar: [18.5018, 73.926],
  Wagholi: [18.5617, 73.9757],
  Talegaon: [18.7332, 73.6723],
  Chakan: [18.7601, 73.8637],
  Shivajinagar: [18.5308, 73.8474],
  Aundh: [18.5578, 73.8073],
  "Viman Nagar": [18.5679, 73.9143],
  Pimpri: [18.6279, 73.7997],
  Chinchwad: [18.6436, 73.7983],
  Katraj: [18.4601, 73.8669],
  Ambegaon: [18.4489, 73.8526],
  "Kalyani Nagar": [18.5456, 73.901],
  Magarpatta: [18.5114, 73.9274],
  Bavdhan: [18.5196, 73.7805],
  Kondhwa: [18.4672, 73.8924],
  Nibm: [18.4608, 73.898],
  Dhanori: [18.5896, 73.9155],
  Vishrantwadi: [18.581, 73.901],
  Ravet: [18.6434, 73.7449],
  Undri: [18.4524, 73.9009],
  Fursungi: [18.4842, 73.9279],
  // Mumbai
  "Bandra West": [19.0596, 72.8295],
  Worli: [19.0176, 72.8149],
  Powai: [19.1176, 72.906],
  "Andheri West": [19.1362, 72.8296],
  "Andheri East": [19.1136, 72.8697],
  Thane: [19.2183, 72.9781],
  "Navi Mumbai": [19.0368, 73.0158],
  Dadar: [19.0178, 72.8478],
  Borivali: [19.2307, 72.8567],
  "Mira Road": [19.2813, 72.8742],
  Virar: [19.4588, 72.8139],
  Kharghar: [19.0474, 73.0659],
  Goregaon: [19.1663, 72.8526],
  Malad: [19.1872, 72.8484],
  Kandivali: [19.2071, 72.8546],
  Kurla: [19.0726, 72.8826],
  Ghatkopar: [19.0867, 72.9082],
  Mulund: [19.1726, 72.956],
  Chembur: [19.0522, 72.8994],
  Panvel: [18.9894, 73.1175],
  // Bangalore
  Koramangala: [12.9352, 77.6245],
  Indiranagar: [12.9719, 77.6412],
  Whitefield: [12.9698, 77.7499],
  "HSR Layout": [12.9116, 77.6389],
  "Electronic City": [12.8399, 77.677],
  Marathahalli: [12.9591, 77.6974],
  "Sarjapur Road": [12.9102, 77.6846],
  Yelahanka: [13.1005, 77.5963],
  Bannerghatta: [12.8002, 77.5773],
  Devanahalli: [13.2476, 77.7179],
  "Tumkur Road": [13.0358, 77.526],
  Jayanagar: [12.9259, 77.5937],
  "JP Nagar": [12.9067, 77.5856],
  Hebbal: [13.0358, 77.597],
  Rajajinagar: [12.9913, 77.556],
  Banashankari: [12.9249, 77.5468],
  "Kanakapura Road": [12.8724, 77.5581],
};

/**
 * Returns the name of the closest known locality to [lat, lon].
 * Also returns the distance in km.
 */
export function findNearestLocality(lat, lon) {
  let best = null;
  let bestDist = Infinity;
  for (const [name, coords] of Object.entries(LOCALITY_COORDS)) {
    const d = haversine([lat, lon], coords);
    if (d < bestDist) {
      bestDist = d;
      best = name;
    }
  }
  return { locality: best, distanceKm: bestDist };
}

/**
 * Geocode a free-text address via Nominatim.
 * Returns { lat, lon, display } or null.
 */
export async function geocodeAddress(address) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(address)}`;
  const res = await fetch(url, { headers: { "Accept-Language": "en" } });
  const data = await res.json();
  if (!data.length) return null;
  return {
    lat: parseFloat(data[0].lat),
    lon: parseFloat(data[0].lon),
    display: data[0].display_name,
  };
}
/**
 * Reverse geocode lat/lon to a human-readable address via Nominatim.
 * Returns the display_name string or a fallback coordinate string.
 */
export async function reverseGeocode(lat, lon) {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=17&addressdetails=1`;
    const res = await fetch(url, { headers: { "Accept-Language": "en" } });
    const data = await res.json();
    if (data && data.display_name) {
      // Return a concise address: road + suburb + city
      const a = data.address || {};
      const parts = [
        a.road || a.pedestrian || a.footway,
        a.suburb || a.neighbourhood || a.quarter,
        a.city || a.town || a.county,
      ].filter(Boolean);
      return parts.length > 0
        ? parts.join(", ")
        : data.display_name.split(",").slice(0, 3).join(",");
    }
  } catch (_) {}
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
}
