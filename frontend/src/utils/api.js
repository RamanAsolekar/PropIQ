// PropIQ API Client v2 — 3 cities, all endpoints, multi-image support
import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const DEMO_KEY = "propiq-demo-2026";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 300000, // Increased to 5 mins for Render Free Tier ML init
  headers: { "Content-Type": "application/json", "X-API-Key": DEMO_KEY },
});

// ── Core Assessment ────────────────────────────────────────────────────────
export const assessProperty = async (formData) => {
  const { data } = await api.post("/api/v1/assess", formData);
  return data;
};

export const assessFull = async (formData) => {
  const { data } = await api.post("/api/v1/assess/full", formData);
  return data;
};

/**
 * Multi-image assessment.
 * images: Array of { file: File, tag: 'exterior'|'interior' }
 */
export const assessWithImages = async (formData, images = []) => {
  const fd = new FormData();
  Object.entries(formData).forEach(([k, v]) => fd.append(k, v));

  if (images.length === 1) {
    // Keep backward-compat single field
    fd.append("image", images[0].file);
  } else {
    images.forEach((img, i) => {
      fd.append("images", img.file);
      fd.append(`image_tag_${i}`, img.tag || "exterior");
    });
  }

  const { data } = await axios.post(`${BASE_URL}/api/v1/assess/image`, fd, {
    headers: { "Content-Type": "multipart/form-data", "X-API-Key": DEMO_KEY },
    timeout: 300000, // 5 mins allowed for CLIP image processing on free tier
  });
  return data;
};

// Legacy single-image compat
export const assessWithImage = async (formData, imageFile) =>
  assessWithImages(formData, [{ file: imageFile, tag: "exterior" }]);

export const downloadPDF = async (formData) => {
  const hasAssessmentPayload =
    formData && formData.market_value_mid && formData.request_id;
  const endpoint = hasAssessmentPayload
    ? "/api/v1/assess/pdf/result"
    : "/api/v1/assess/pdf";
  const { data } = await api.post(endpoint, formData, { responseType: "blob" });
  const url = window.URL.createObjectURL(
    new Blob([data], { type: "application/pdf" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute(
    "download",
    `PropIQ_Report_${formData.locality || "Property"}_${Date.now()}.pdf`,
  );
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const getNarration = async (formData) => {
  const { data } = await api.post("/api/v1/assess/narrate", formData);
  return data;
};

// ── Reference Data ─────────────────────────────────────────────────────────
export const getLocalities = async (city) => {
  const { data } = await api.get("/api/v1/localities", {
    params: city ? { city } : {},
  });
  return data;
};

export const getComps = async (locality, propType, sizeSqft, ageYears) => {
  const { data } = await api.get("/api/v1/comps", {
    params: {
      locality,
      prop_type: propType,
      size_sqft: sizeSqft,
      age_years: ageYears,
      n: 5,
    },
  });
  return data;
};

export const getTrend = async (locality, propType) => {
  const { data } = await api.get(
    `/api/v1/trends/${encodeURIComponent(locality)}`,
    { params: { prop_type: propType } },
  );
  return data;
};

export const getAuditLog = async () => {
  const { data } = await api.get("/api/v1/audit/recent", {
    params: { limit: 10 },
  });
  return data;
};

// ── Deep AIML capabilities ──────────────────────────────────────────────────

// Agentic, tool-calling valuation with a hallucination verifier
export const assessWithAgent = async (formData) => {
  const { data } = await api.post("/api/v1/assess/agent", formData);
  return data;
};

// RAG: query the policy/knowledge base
export const ragQuery = async (query, k) => {
  const { data } = await api.post("/api/v1/rag/query", { query, k });
  return data;
};

export const ragStats = async () => {
  const { data } = await api.get("/api/v1/rag/stats");
  return data;
};

// Learned price forecast (+ confidence band)
export const getForecast = async (locality, propType, horizon = 6) => {
  const { data } = await api.get(
    `/api/v1/forecast/${encodeURIComponent(locality)}`,
    { params: { prop_type: propType, horizon } },
  );
  return data;
};

// Vector duplicate / fraud detection
export const checkDuplicate = async (formData) => {
  const { data } = await api.post("/api/v1/fraud/duplicate-check", formData);
  return data;
};

export const getFraudRings = async () => {
  const { data } = await api.get("/api/v1/fraud/rings");
  return data;
};

// Knowledge graph: portfolio concentration + developer propagation
export const getConcentration = async () => {
  const { data } = await api.get("/api/v1/graph/concentration");
  return data;
};

export const getDeveloperPropagation = async () => {
  const { data } = await api.get("/api/v1/graph/developer-propagation");
  return data;
};

// Fair-lending bias audit
export const getFairnessAudit = async () => {
  const { data } = await api.get("/api/v1/ml/fairness");
  return data;
};

// MLOps: registry, performance, drift
export const getModelRegistry = async () => {
  const { data } = await api.get("/api/v1/ml/registry");
  return data;
};

export const getModelPerformance = async () => {
  const { data } = await api.get("/api/v1/ml/performance");
  return data;
};

export const getDriftReport = async () => {
  const { data } = await api.get("/api/v1/ml/drift");
  return data;
};

// SSE helpers — stream the credit memo / agent trace via fetch + ReadableStream.
// (EventSource only supports GET; these endpoints are POST, so we stream fetch.)
export const streamCreditMemo = async (formData, onEvent) => {
  const resp = await fetch(`${BASE_URL}/api/v1/assess/narrate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": DEMO_KEY },
    body: JSON.stringify(formData),
  });
  await consumeSSE(resp, onEvent);
};

export const streamAgent = async (formData, onEvent) => {
  const resp = await fetch(`${BASE_URL}/api/v1/agent/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": DEMO_KEY },
    body: JSON.stringify(formData),
  });
  await consumeSSE(resp, onEvent);
};

// Live portfolio health stream (GET => can also use EventSource)
export const streamPortfolio = (onEvent) => {
  const es = new EventSource(
    `${BASE_URL}/api/v1/portfolio/stream`,
    { withCredentials: false },
  );
  es.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data));
    } catch {
      /* ignore */
    }
  };
  return es; // caller calls es.close()
};

async function consumeSSE(resp, onEvent) {
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop();
    for (const part of parts) {
      const line = part.replace(/^data:\s?/, "").trim();
      if (!line) continue;
      try {
        onEvent(JSON.parse(line));
      } catch {
        onEvent({ raw: line });
      }
    }
  }
}

// ── Async Batch (Celery) ───────────────────────────────────────────────────
export const submitBatchAsync = async (properties) => {
  const { data } = await api.post("/api/v1/assess/batch/async", properties);
  return data;
};

export const pollBatchStatus = async (jobId) => {
  const { data } = await api.get(`/api/v1/batch/status/${jobId}`);
  return data;
};

export const healthCheck = async () => {
  const { data } = await api.get("/api/v1/health");
  return data;
};

// ── Formatters ─────────────────────────────────────────────────────────────
export const formatINR = (value) => {
  if (!value && value !== 0) return "—";
  if (value >= 10_000_000) return `₹${(value / 10_000_000).toFixed(2)} Cr`;
  if (value >= 100_000) return `₹${(value / 100_000).toFixed(2)} L`;
  return `₹${value.toLocaleString("en-IN")}`;
};

export const formatINRShort = (value) => {
  if (!value && value !== 0) return "—";
  if (value >= 10_000_000) return `₹${(value / 10_000_000).toFixed(1)}Cr`;
  if (value >= 100_000) return `₹${(value / 100_000).toFixed(1)}L`;
  return `₹${value.toLocaleString("en-IN")}`;
};

// ── Constants ──────────────────────────────────────────────────────────────
export const PROP_TYPES = [
  { value: "1bhk_apartment", label: "1 BHK Apartment" },
  { value: "2bhk_apartment", label: "2 BHK Apartment" },
  { value: "3bhk_apartment", label: "3 BHK Apartment" },
  { value: "4bhk_apartment", label: "4 BHK Apartment" },
  { value: "villa", label: "Villa / Bungalow" },
  { value: "shop", label: "Commercial Shop" },
  { value: "office", label: "Office Space" },
  { value: "plot", label: "Plot / Land" },
  { value: "warehouse", label: "Industrial Warehouse" },
  { value: "factory", label: "Factory / Industrial Unit" },
];

export const LOCALITIES_BY_CITY = {
  Pune: [
    "Koregaon Park",
    "Shivajinagar",
    "Baner",
    "Kothrud",
    "Aundh",
    "Viman Nagar",
    "Wakad",
    "Hinjewadi",
    "Hadapsar",
    "Pimpri",
    "Chinchwad",
    "Katraj",
    "Wagholi",
    "Talegaon",
    "Chakan",
    "Ambegaon",
  ],
  Mumbai: [
    "Bandra West",
    "Worli",
    "Powai",
    "Andheri West",
    "Andheri East",
    "Thane",
    "Navi Mumbai",
    "Dadar",
    "Borivali",
    "Mira Road",
    "Virar",
    "Kharghar",
  ],
  Bangalore: [
    "Koramangala",
    "Indiranagar",
    "Whitefield",
    "HSR Layout",
    "Electronic City",
    "Marathahalli",
    "Sarjapur Road",
    "Yelahanka",
    "Bannerghatta",
    "Devanahalli",
    "Tumkur Road",
  ],
};

export const ALL_LOCALITIES = Object.values(LOCALITIES_BY_CITY).flat();
