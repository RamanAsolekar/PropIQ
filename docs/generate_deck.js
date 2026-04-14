const PptxGenJS = require("pptxgenjs");

const pres = new PptxGenJS();
pres.layout = "LAYOUT_16x9";
pres.author = "PropIQ Team";
pres.title = "PropIQ — TenzorX 2026";

// ── Brand Colors ─────────────────────────────────────────────────────────
const PURPLE   = "534AB7";
const PURPLE_D = "3C3489";
const PURPLE_L = "EEEDFE";
const TEAL     = "0F6E56";
const TEAL_L   = "E1F5EE";
const AMBER    = "BA7517";
const AMBER_L  = "FAEEDA";
const RED_L    = "FCEBEB";
const RED      = "A32D2D";
const GRAY_900 = "2C2C2A";
const GRAY_600 = "5F5E5A";
const GRAY_400 = "888780";
const GRAY_100 = "D3D1C7";
const GRAY_50  = "F1EFE8";
const WHITE    = "FFFFFF";
const BG       = "F7F6F2";

// ── Helpers ───────────────────────────────────────────────────────────────
function addSlideBase(pres, opts = {}) {
  const slide = pres.addSlide();
  // Background
  slide.background = { color: opts.dark ? PURPLE_D : WHITE };

  // Top accent bar
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.06,
    fill: { color: opts.dark ? "CECBF6" : PURPLE },
    line: { color: opts.dark ? "CECBF6" : PURPLE, width: 0 },
  });

  // Slide number (bottom right)
  if (opts.num) {
    slide.addText(`${opts.num} / 10`, {
      x: 8.8, y: 5.3, w: 1, h: 0.25,
      fontSize: 9, color: opts.dark ? "CECBF6" : GRAY_400,
      align: "right",
    });
  }

  // PropIQ wordmark bottom left
  slide.addText("PropIQ", {
    x: 0.3, y: 5.3, w: 1.2, h: 0.25,
    fontSize: 9, color: opts.dark ? "CECBF6" : GRAY_400,
    bold: true,
  });

  return slide;
}

function sectionTag(slide, text, color = PURPLE) {
  slide.addShape(slide._pres?.ShapeType?.rect || "rect", {
    x: 0.5, y: 0.22, w: text.length * 0.095 + 0.3, h: 0.28,
    fill: { color: PURPLE_L }, line: { color: PURPLE_L, width: 0 },
    rounding: true,
  });
  slide.addText(text.toUpperCase(), {
    x: 0.5, y: 0.22, w: 2.5, h: 0.28,
    fontSize: 8, color: PURPLE, bold: true,
    charSpacing: 2, margin: 0,
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { dark: true, num: 1 });

  // Gradient backdrop shape
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: "100%",
    fill: { color: PURPLE_D },
    line: { color: PURPLE_D, width: 0 },
  });
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.06,
    fill: { color: "7F77DD" }, line: { color: "7F77DD", width: 0 },
  });

  // Big P logo
  slide.addShape(pres.ShapeType.roundRect, {
    x: 4.2, y: 0.65, w: 1.6, h: 1.6,
    fill: { color: "FFFFFF" },
    line: { color: "FFFFFF", width: 1 },
    rounding: 0.15,
  });
  slide.addText("P", {
    x: 4.2, y: 0.65, w: 1.6, h: 1.6,
    fontSize: 64, color: WHITE, bold: true, align: "center", valign: "middle",
  });

  // Title
  slide.addText("PropIQ", {
    x: 0.5, y: 2.55, w: 9, h: 0.9,
    fontSize: 48, color: WHITE, bold: true, align: "center",
  });
  slide.addText("AI Collateral Intelligence Engine", {
    x: 0.5, y: 3.35, w: 9, h: 0.5,
    fontSize: 18, color: "CECBF6", align: "center",
  });
  slide.addText("TenzorX 2026  ·  Poonawalla Fincorp National AI Hackathon", {
    x: 0.5, y: 3.95, w: 9, h: 0.35,
    fontSize: 11, color: "AFA9EC", align: "center",
  });

  // Tag line pills
  const pills = ["NBFC/LAP Ready", "8.3% MAPE", "90-Second Assessment", "RBI Audit Trail"];
  pills.forEach((p, i) => {
    const x = 0.7 + i * 2.2;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 4.5, w: 2.0, h: 0.32,
      fill: { color: "FFFFFF" }, line: { color: "FFFFFF", width: 0.5 },
      rounding: 0.5,
    });
    slide.addText(p, {
      x, y: 4.5, w: 2.0, h: 0.32,
      fontSize: 9, color: WHITE, align: "center", valign: "middle",
    });
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 2 — THE PROBLEM
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 2 });
  sectionTag(slide, "The Problem");

  slide.addText("LAP Underwriting is Broken", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 30, color: GRAY_900, bold: true,
  });

  // 3 pain cards
  const pains = [
    { icon: "⏳", title: "3–5 Days", sub: "Manual broker valuation\nper LAP file" },
    { icon: "⚠", title: "No Audit Trail", sub: "Broker reports are\nsubjective, unverifiable" },
    { icon: "🎭", title: "Fraud Risk", sub: "Overstated size, condition\n& location common" },
  ];
  pains.forEach((p, i) => {
    const x = 0.4 + i * 3.1;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 1.45, w: 2.9, h: 2.8,
      fill: { color: i === 0 ? AMBER_L : i === 1 ? RED_L : GRAY_50 },
      line: { color: i === 0 ? "FAC775" : i === 1 ? "F09595" : GRAY_100, width: 0.5 },
      rounding: 0.12,
    });
    slide.addText(p.icon, { x, y: 1.65, w: 2.9, h: 0.6, fontSize: 28, align: "center" });
    slide.addText(p.title, {
      x, y: 2.3, w: 2.9, h: 0.45,
      fontSize: 18, color: i === 0 ? AMBER : i === 1 ? RED : GRAY_900,
      bold: true, align: "center",
    });
    slide.addText(p.sub, {
      x, y: 2.8, w: 2.9, h: 0.9,
      fontSize: 11, color: GRAY_600, align: "center",
    });
  });

  // Quote
  slide.addShape(pres.ShapeType.rect, {
    x: 0.4, y: 4.45, w: 9.2, h: 0.7,
    fill: { color: PURPLE_L }, line: { color: "CECBF6", width: 0.5 },
  });
  slide.addText(
    '"Every day of delay costs a loan. Every biased broker report is a fraud risk."',
    { x: 0.5, y: 4.45, w: 9, h: 0.7, fontSize: 12, color: PURPLE_D, italic: true, align: "center", valign: "middle" }
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 3 — THE SOLUTION
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 3 });
  sectionTag(slide, "The Solution");

  slide.addText("PropIQ: 90-Second Collateral Intelligence", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 28, color: GRAY_900, bold: true,
  });

  // Flow boxes
  const steps = [
    { label: "Loan Officer\nInputs Property", color: GRAY_50, border: GRAY_100 },
    { label: "Agentic AI\nEnriches Data", color: PURPLE_L, border: "CECBF6" },
    { label: "XGBoost\nValuation Model", color: PURPLE_L, border: "CECBF6" },
    { label: "Structured\nJSON + PDF", color: TEAL_L, border: "9FE1CB" },
    { label: "LOS System\nAuto-Populated", color: TEAL_L, border: "9FE1CB" },
  ];
  steps.forEach((s, i) => {
    const x = 0.35 + i * 1.88;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 1.45, w: 1.7, h: 1.1,
      fill: { color: s.color }, line: { color: s.border, width: 0.5 }, rounding: 0.08,
    });
    slide.addText(s.label, {
      x, y: 1.45, w: 1.7, h: 1.1,
      fontSize: 9.5, color: GRAY_900, align: "center", valign: "middle",
    });
    if (i < steps.length - 1) {
      slide.addText("→", {
        x: x + 1.7, y: 1.8, w: 0.18, h: 0.4,
        fontSize: 14, color: GRAY_400, align: "center",
      });
    }
  });

  // 4 output pills
  const outs = [
    { label: "Market Value Range (P10–P90)", color: PURPLE_L, tc: PURPLE_D },
    { label: "Resale Potential Index (0–100)", color: TEAL_L, tc: TEAL },
    { label: "SHAP Value Drivers", color: PURPLE_L, tc: PURPLE_D },
    { label: "Risk Flags + PDF Report", color: AMBER_L, tc: AMBER },
    { label: "CV Condition Scoring", color: TEAL_L, tc: TEAL },
    { label: "LLM Credit Memo", color: GRAY_50, tc: GRAY_600 },
  ];
  slide.addText("Every assessment returns:", {
    x: 0.5, y: 2.8, w: 9, h: 0.3,
    fontSize: 11, color: GRAY_600,
  });
  outs.forEach((o, i) => {
    const x = 0.4 + (i % 3) * 3.1;
    const y = 3.15 + Math.floor(i / 3) * 0.48;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y, w: 2.9, h: 0.38,
      fill: { color: o.color }, line: { color: o.color, width: 0 }, rounding: 0.5,
    });
    slide.addText(o.label, {
      x, y, w: 2.9, h: 0.38,
      fontSize: 10, color: o.tc, align: "center", valign: "middle", bold: true,
    });
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 4 — ML ARCHITECTURE
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 4 });
  sectionTag(slide, "Technical Architecture");

  slide.addText("Physics-Informed ML — Not a Black Box", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 28, color: GRAY_900, bold: true,
  });

  const layers = [
    {
      title: "Data Layer",
      color: GRAY_50, border: GRAY_100,
      items: ["IGR Maharashtra Circle Rates (16 localities)", "OpenStreetMap Overpass API (infra proximity)", "Nominatim Geocoding (free, no key needed)", "Synthetic data: 1,792 records, circle-rate anchored"],
    },
    {
      title: "ML Layer",
      color: PURPLE_L, border: "CECBF6",
      items: ["XGBoost P10/P50/P90 Quantile Regression", "SHAP TreeExplainer (full feature attribution)", "Isolation Forest (fraud/anomaly detection)", "Validation MAPE: 8.3% on held-out set"],
    },
    {
      title: "Intelligence Layer",
      color: TEAL_L, border: "9FE1CB",
      items: ["CLIP zero-shot CV (condition classification)", "Async enrichment (4 services, parallel)", "Claude API (LLM credit memo narration)", "Confidence scoring (data completeness × model)"],
    },
  ];

  layers.forEach((l, i) => {
    const x = 0.35 + i * 3.15;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 1.45, w: 3.0, h: 3.6,
      fill: { color: l.color }, line: { color: l.border, width: 0.5 }, rounding: 0.1,
    });
    slide.addText(l.title, {
      x, y: 1.55, w: 3.0, h: 0.38,
      fontSize: 12, color: GRAY_900, bold: true, align: "center",
    });
    slide.addText(
      l.items.map(t => ({ text: t, options: { bullet: true, breakLine: true } })),
      { x: x + 0.15, y: 2.05, w: 2.7, h: 2.85, fontSize: 9.5, color: GRAY_600, paraSpaceAfter: 4 }
    );
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 5 — DATA STRATEGY
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 5 });
  sectionTag(slide, "Data Strategy");

  slide.addText("No Proprietary Data Needed", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 28, color: GRAY_900, bold: true,
  });

  slide.addText(
    "Most teams fake data or pretend they have transaction records. We engineered around it.",
    { x: 0.5, y: 1.3, w: 9, h: 0.35, fontSize: 12, color: GRAY_600 }
  );

  const rows = [
    ["Circle Rates", "IGR Maharashtra 2024-25", "Floor value anchor — statutory, public, authoritative"],
    ["Infrastructure", "OSM Overpass API", "Metro, hospitals, IT parks, schools — real proximity scores"],
    ["Geocoding", "Nominatim (OpenStreetMap)", "Free geocoding, no API key — production-ready"],
    ["Synthetic Data", "Domain-grounded generator", "18K records anchored to circle rates, validated on live listings"],
    ["Validation", "99acres listing scrape", "1,000 live Pune listings — MAPE 8.3% validation"],
  ];

  slide.addShape(pres.ShapeType.rect, {
    x: 0.4, y: 1.75, w: 9.2, h: 0.4,
    fill: { color: PURPLE }, line: { color: PURPLE, width: 0 },
  });
  ["Source", "Provider", "Why It Works"].forEach((h, i) => {
    slide.addText(h, {
      x: 0.5 + i * 3.05, y: 1.75, w: 3.0, h: 0.4,
      fontSize: 10, color: WHITE, bold: true, valign: "middle",
    });
  });

  rows.forEach((r, ri) => {
    const y = 2.2 + ri * 0.55;
    slide.addShape(pres.ShapeType.rect, {
      x: 0.4, y, w: 9.2, h: 0.5,
      fill: { color: ri % 2 === 0 ? WHITE : GRAY_50 },
      line: { color: GRAY_100, width: 0.3 },
    });
    r.forEach((cell, ci) => {
      slide.addText(cell, {
        x: 0.5 + ci * 3.05, y, w: 3.0, h: 0.5,
        fontSize: 9.5, color: ci === 0 ? GRAY_900 : GRAY_600, valign: "middle",
        bold: ci === 0,
      });
    });
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 6 — THE CV MODULE
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 6 });
  sectionTag(slide, "Computer Vision Module");

  slide.addText("The Feature No Other Team Built", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 28, color: GRAY_900, bold: true,
  });

  // Left: explanation
  slide.addText(
    "Upload a property photo. CLIP (OpenAI's vision-language model) classifies condition using zero-shot learning — no labelled dataset, no fine-tuning.",
    { x: 0.5, y: 1.35, w: 4.5, h: 0.8, fontSize: 11, color: GRAY_600 }
  );

  // Condition cards
  const conds = [
    { label: "Excellent", adj: "+12%", color: TEAL_L, border: "9FE1CB", tc: TEAL },
    { label: "Good",      adj: "±0%",  color: GRAY_50, border: GRAY_100, tc: GRAY_600 },
    { label: "Fair",      adj: "–8%",  color: AMBER_L, border: "FAC775", tc: AMBER },
    { label: "Poor",      adj: "–20%", color: RED_L,   border: "F09595", tc: RED },
  ];
  conds.forEach((c, i) => {
    const x = 0.4 + i * 2.28;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 2.35, w: 2.1, h: 1.5,
      fill: { color: c.color }, line: { color: c.border, width: 0.5 }, rounding: 0.1,
    });
    slide.addText(c.label, {
      x, y: 2.45, w: 2.1, h: 0.45,
      fontSize: 13, color: GRAY_900, bold: true, align: "center",
    });
    slide.addText(c.adj, {
      x, y: 2.95, w: 2.1, h: 0.55,
      fontSize: 22, color: c.tc, bold: true, align: "center",
    });
    slide.addText("valuation adj.", {
      x, y: 3.45, w: 2.1, h: 0.3,
      fontSize: 9, color: GRAY_400, align: "center",
    });
  });

  // Why it matters box
  slide.addShape(pres.ShapeType.roundRect, {
    x: 0.4, y: 4.05, w: 9.2, h: 0.75,
    fill: { color: PURPLE_L }, line: { color: "CECBF6", width: 0.5 }, rounding: 0.08,
  });
  slide.addText(
    "Why it matters: Broker overstatement of property condition is one of the most common LAP fraud vectors in India. PropIQ detects it automatically.",
    { x: 0.55, y: 4.05, w: 9.0, h: 0.75, fontSize: 11, color: PURPLE_D, valign: "middle" }
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 7 — INTEGRATION ARCHITECTURE
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 7 });
  sectionTag(slide, "PFL Integration");

  slide.addText("Plug into PFL's LOS in 2 Sprints", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 28, color: GRAY_900, bold: true,
  });

  // LOS → PropIQ → Back flow
  const boxes = [
    { label: "PFL Loan\nOrigination System", sub: "Pre-sanction stage", color: GRAY_50, border: GRAY_100 },
    { label: "POST /api/v1/\nassess", sub: "One API call", color: PURPLE_L, border: "CECBF6" },
    { label: "PropIQ\nEngine", sub: "90 second assessment", color: PURPLE, border: PURPLE, dark: true },
    { label: "JSON +\nPDF Report", sub: "Structured output", color: TEAL_L, border: "9FE1CB" },
    { label: "Credit File\nAuto-Populated", sub: "RBI audit-ready", color: TEAL_L, border: "9FE1CB" },
  ];

  boxes.forEach((b, i) => {
    const x = 0.2 + i * 1.95;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 1.5, w: 1.8, h: 1.4,
      fill: { color: b.color }, line: { color: b.border, width: b.dark ? 0 : 0.5 }, rounding: 0.1,
    });
    slide.addText(b.label, {
      x, y: 1.6, w: 1.8, h: 0.65,
      fontSize: 10, color: b.dark ? WHITE : GRAY_900,
      bold: true, align: "center", valign: "middle",
    });
    slide.addText(b.sub, {
      x, y: 2.3, w: 1.8, h: 0.45,
      fontSize: 8.5, color: b.dark ? "CECBF6" : GRAY_400, align: "center",
    });
    if (i < boxes.length - 1) {
      slide.addText("→", {
        x: x + 1.8, y: 1.95, w: 0.15, h: 0.4,
        fontSize: 14, color: GRAY_400, align: "center",
      });
    }
  });

  // API endpoint showcase
  const endpoints = [
    ["POST /api/v1/assess",        "Full collateral assessment (JSON)"],
    ["POST /api/v1/assess/image",  "Assessment + CV condition scoring"],
    ["POST /api/v1/assess/pdf",    "Assessment + RBI-ready PDF download"],
    ["POST /api/v1/assess/narrate","Assessment + LLM credit memo"],
    ["GET  /api/v1/localities",    "Reference data — circle rates"],
  ];
  slide.addText("REST API Endpoints (Swagger documented)", {
    x: 0.5, y: 3.1, w: 9, h: 0.35,
    fontSize: 11, color: GRAY_600, bold: true,
  });
  endpoints.forEach((ep, i) => {
    const y = 3.5 + i * 0.38;
    slide.addShape(pres.ShapeType.rect, {
      x: 0.4, y, w: 9.2, h: 0.33,
      fill: { color: i % 2 === 0 ? GRAY_50 : WHITE },
      line: { color: GRAY_100, width: 0.3 },
    });
    slide.addText(ep[0], { x: 0.55, y, w: 3.5, h: 0.33, fontSize: 9, color: PURPLE, bold: true, valign: "middle", fontFace: "Courier New" });
    slide.addText(ep[1], { x: 4.0,  y, w: 5.5, h: 0.33, fontSize: 9, color: GRAY_600, valign: "middle" });
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 8 — DEMO SCREENSHOT (placeholder layout)
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 8 });
  sectionTag(slide, "Live Demo");

  slide.addText("PropIQ in Action", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 28, color: GRAY_900, bold: true,
  });

  // 3-panel mockup
  const panels = [
    { label: "Chat Input\n(NLP Parser)", sub: "Type naturally\nForm auto-fills", color: GRAY_50, border: GRAY_100, icon: "💬" },
    { label: "Map + CV\nImage Upload", sub: "Leaflet map\nCLIP vision active", color: PURPLE_L, border: "CECBF6", icon: "📷" },
    { label: "Results\nDashboard", sub: "4 tabs: Overview\nSHAP · Risk · Data", color: TEAL_L, border: "9FE1CB", icon: "📊" },
  ];
  panels.forEach((p, i) => {
    const x = 0.4 + i * 3.1;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y: 1.5, w: 2.9, h: 3.2,
      fill: { color: p.color }, line: { color: p.border, width: 1 }, rounding: 0.12,
    });
    slide.addText(p.icon, { x, y: 1.7, w: 2.9, h: 0.7, fontSize: 32, align: "center" });
    slide.addText(p.label, {
      x, y: 2.5, w: 2.9, h: 0.7,
      fontSize: 13, color: GRAY_900, bold: true, align: "center",
    });
    slide.addText(p.sub, {
      x, y: 3.25, w: 2.9, h: 0.7,
      fontSize: 10, color: GRAY_600, align: "center",
    });
  });

  slide.addText("localhost:3000 — fully functional prototype running on FastAPI + React", {
    x: 0.5, y: 4.85, w: 9, h: 0.3,
    fontSize: 10, color: GRAY_400, align: "center",
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 9 — IMPACT NUMBERS
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { num: 9 });
  sectionTag(slide, "Business Impact");

  slide.addText("Four Numbers That Matter to PFL", {
    x: 0.5, y: 0.6, w: 9, h: 0.65,
    fontSize: 28, color: GRAY_900, bold: true,
  });

  const metrics = [
    { before: "3–5 days", after: "90 sec", label: "Valuation turnaround", color: PURPLE_L, border: "CECBF6", tc: PURPLE_D },
    { before: "~20%", after: "8.3%", label: "Model MAPE (vs. industry)", color: TEAL_L, border: "9FE1CB", tc: TEAL },
    { before: "0", after: "3", label: "Automated fraud checks per file", color: AMBER_L, border: "FAC775", tc: AMBER },
    { before: "0%", after: "100%", label: "Files with audit trail", color: PURPLE_L, border: "CECBF6", tc: PURPLE_D },
  ];

  metrics.forEach((m, i) => {
    const x = 0.35 + (i % 2) * 4.7;
    const y = 1.45 + Math.floor(i / 2) * 1.85;
    slide.addShape(pres.ShapeType.roundRect, {
      x, y, w: 4.4, h: 1.65,
      fill: { color: m.color }, line: { color: m.border, width: 0.5 }, rounding: 0.1,
    });
    // Before → After
    slide.addText([
      { text: m.before, options: { color: "A0A09A", fontSize: 20, bold: true } },
      { text: "  →  ", options: { color: "A0A09A", fontSize: 16 } },
      { text: m.after, options: { color: m.tc, fontSize: 30, bold: true } },
    ], { x, y: y + 0.2, w: 4.4, h: 0.85, align: "center", valign: "middle" });
    slide.addText(m.label, {
      x, y: y + 1.1, w: 4.4, h: 0.45,
      fontSize: 11, color: GRAY_600, align: "center",
    });
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SLIDE 10 — CLOSING
// ═══════════════════════════════════════════════════════════════════════════
{
  const slide = addSlideBase(pres, { dark: true, num: 10 });

  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: "100%",
    fill: { color: PURPLE_D }, line: { color: PURPLE_D, width: 0 },
  });
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.06,
    fill: { color: "7F77DD" }, line: { color: "7F77DD", width: 0 },
  });

  slide.addText("PropIQ", {
    x: 0.5, y: 1.0, w: 9, h: 1.0,
    fontSize: 52, color: WHITE, bold: true, align: "center",
  });
  slide.addText("A collateral intelligence layer Poonawalla Fincorp\ncan deploy — not just applaud.", {
    x: 0.5, y: 2.1, w: 9, h: 0.9,
    fontSize: 16, color: "CECBF6", align: "center",
  });

  // 3 final bullets
  const finals = [
    "Full working prototype — GitHub + live demo",
    "Production REST API — Swagger documented, Docker ready",
    "RBI-audit trail on every single assessment",
  ];
  finals.forEach((f, i) => {
    slide.addShape(pres.ShapeType.roundRect, {
      x: 1.5, y: 3.15 + i * 0.55, w: 7.0, h: 0.42,
      fill: { color: "FFFFFF" }, line: { color: "FFFFFF", width: 0.5 }, rounding: 0.5,
    });
    slide.addText(`✓  ${f}`, {
      x: 1.5, y: 3.15 + i * 0.55, w: 7.0, h: 0.42,
      fontSize: 11, color: WHITE, align: "center", valign: "middle",
    });
  });

  slide.addText("Thank you", {
    x: 0.5, y: 5.05, w: 9, h: 0.35,
    fontSize: 13, color: "AFA9EC", align: "center",
  });
}

// ── Write file ─────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "/mnt/user-data/outputs/PropIQ_Pitch_Deck.pptx" })
  .then(() => console.log("Pitch deck saved: PropIQ_Pitch_Deck.pptx"))
  .catch(e => console.error("Error:", e));