// PropIQ Chat Parser
// Converts natural language input into structured property fields
// Runs client-side — no extra API call needed

const LOCALITY_LIST = [
  // Pune (indices 0-25 → 26 entries)
  "koregaon park",
  "shivajinagar",
  "baner",
  "kothrud",
  "aundh",
  "viman nagar",
  "kalyani nagar",
  "magarpatta",
  "bavdhan",
  "wakad",
  "hinjewadi",
  "hadapsar",
  "pimpri",
  "chinchwad",
  "katraj",
  "kondhwa",
  "nibm",
  "dhanori",
  "vishrantwadi",
  "ravet",
  "wagholi",
  "talegaon",
  "chakan",
  "ambegaon",
  "undri",
  "fursungi",
  // Mumbai (indices 26-45 → 20 entries)
  "bandra west",
  "bandra",
  "worli",
  "powai",
  "andheri west",
  "andheri east",
  "andheri",
  "dadar",
  "thane",
  "navi mumbai",
  "borivali",
  "goregaon",
  "malad",
  "kandivali",
  "kurla",
  "ghatkopar",
  "mulund",
  "chembur",
  "kharghar",
  "mira road",
  "virar",
  "panvel",
  // Bangalore (index 48+)
  "koramangala",
  "indiranagar",
  "whitefield",
  "hsr layout",
  "hsr",
  "jayanagar",
  "jp nagar",
  "electronic city",
  "marathahalli",
  "sarjapur road",
  "sarjapur",
  "hebbal",
  "rajajinagar",
  "banashankari",
  "yelahanka",
  "bannerghatta",
  "devanahalli",
  "tumkur road",
  "kanakapura road",
];

const LOCALITY_DISPLAY = {
  // Pune
  "koregaon park": "Koregaon Park",
  shivajinagar: "Shivajinagar",
  baner: "Baner",
  kothrud: "Kothrud",
  aundh: "Aundh",
  "viman nagar": "Viman Nagar",
  "kalyani nagar": "Kalyani Nagar",
  magarpatta: "Magarpatta",
  bavdhan: "Bavdhan",
  wakad: "Wakad",
  hinjewadi: "Hinjewadi",
  hadapsar: "Hadapsar",
  pimpri: "Pimpri",
  chinchwad: "Chinchwad",
  katraj: "Katraj",
  kondhwa: "Kondhwa",
  nibm: "Nibm",
  dhanori: "Dhanori",
  vishrantwadi: "Vishrantwadi",
  ravet: "Ravet",
  wagholi: "Wagholi",
  talegaon: "Talegaon",
  chakan: "Chakan",
  ambegaon: "Ambegaon",
  undri: "Undri",
  fursungi: "Fursungi",
  // Mumbai
  "bandra west": "Bandra West",
  bandra: "Bandra West",
  worli: "Worli",
  powai: "Powai",
  "andheri west": "Andheri West",
  "andheri east": "Andheri East",
  andheri: "Andheri West",
  dadar: "Dadar",
  thane: "Thane",
  "navi mumbai": "Navi Mumbai",
  borivali: "Borivali",
  goregaon: "Goregaon",
  malad: "Malad",
  kandivali: "Kandivali",
  kurla: "Kurla",
  ghatkopar: "Ghatkopar",
  mulund: "Mulund",
  chembur: "Chembur",
  kharghar: "Kharghar",
  "mira road": "Mira Road",
  virar: "Virar",
  panvel: "Panvel",
  // Bangalore
  koramangala: "Koramangala",
  indiranagar: "Indiranagar",
  whitefield: "Whitefield",
  "hsr layout": "HSR Layout",
  hsr: "HSR Layout",
  jayanagar: "Jayanagar",
  "jp nagar": "JP Nagar",
  "electronic city": "Electronic City",
  marathahalli: "Marathahalli",
  "sarjapur road": "Sarjapur Road",
  sarjapur: "Sarjapur Road",
  hebbal: "Hebbal",
  rajajinagar: "Rajajinagar",
  banashankari: "Banashankari",
  yelahanka: "Yelahanka",
  bannerghatta: "Bannerghatta",
  devanahalli: "Devanahalli",
  "tumkur road": "Tumkur Road",
  "kanakapura road": "Kanakapura Road",
};

export function parsePropertyInput(text) {
  const lower = text.toLowerCase();
  const extracted = {};
  const missing = [];

  // ── Locality ──────────────────────────────────────────────────────────
  for (let i = 0; i < LOCALITY_LIST.length; i++) {
    const loc = LOCALITY_LIST[i];
    if (lower.includes(loc)) {
      extracted.locality = LOCALITY_DISPLAY[loc];
      if (i < 26) extracted.city = "Pune";
      else if (i < 48) extracted.city = "Mumbai";
      else extracted.city = "Bangalore";
      break;
    }
  }
  if (!extracted.locality) missing.push("locality");

  // ── Property type ─────────────────────────────────────────────────────
  if (lower.includes("4bhk") || lower.includes("4 bhk"))
    extracted.prop_type = "4bhk_apartment";
  else if (lower.includes("3bhk") || lower.includes("3 bhk"))
    extracted.prop_type = "3bhk_apartment";
  else if (lower.includes("2bhk") || lower.includes("2 bhk"))
    extracted.prop_type = "2bhk_apartment";
  else if (lower.includes("1bhk") || lower.includes("1 bhk"))
    extracted.prop_type = "1bhk_apartment";
  else if (lower.includes("villa") || lower.includes("bungalow"))
    extracted.prop_type = "villa";
  else if (lower.includes("shop") || lower.includes("commercial"))
    extracted.prop_type = "shop";
  else if (lower.includes("office")) extracted.prop_type = "office";
  else if (lower.includes("plot") || lower.includes("land"))
    extracted.prop_type = "plot";
  if (!extracted.prop_type) missing.push("property type");

  // ── Size ──────────────────────────────────────────────────────────────
  // Matches: "850 sqft", "850sqft", "850 sq ft", "850 sq.ft"
  const sizeMatch = lower.match(
    /(\d[\d,]*)\s*(?:sq\.?\s*ft|sqft|square\s*feet|sft)/,
  );
  if (sizeMatch)
    extracted.size_sqft = parseFloat(sizeMatch[1].replace(",", ""));
  if (!extracted.size_sqft) missing.push("size in sqft");

  // ── Age ───────────────────────────────────────────────────────────────
  // Matches: "5 year old", "5 years", "built in 2018", "new", "under construction"
  const ageMatch = lower.match(/(\d+)\s*(?:year|yr)/);
  if (ageMatch) {
    extracted.age_years = parseInt(ageMatch[1]);
  } else if (lower.includes("new") || lower.includes("under construction")) {
    extracted.age_years = 1;
  } else if (lower.match(/built\s+in\s+(\d{4})/)) {
    const yr = parseInt(lower.match(/built\s+in\s+(\d{4})/)[1]);
    extracted.age_years = Math.max(0, new Date().getFullYear() - yr);
  }
  if (extracted.age_years === undefined) missing.push("building age");

  // ── Floor ─────────────────────────────────────────────────────────────
  const floorMatch = lower.match(/(\d+)(?:st|nd|rd|th)?\s*floor/);
  if (floorMatch) extracted.floor_num = parseInt(floorMatch[1]);
  else if (lower.includes("ground floor")) extracted.floor_num = 0;
  else extracted.floor_num = 3; // default

  // ── Freehold / Leasehold ──────────────────────────────────────────────
  if (lower.includes("leasehold") || lower.includes("lease hold")) {
    extracted.is_freehold = 0;
  } else {
    extracted.is_freehold = 1; // default freehold
  }

  // ── RERA ──────────────────────────────────────────────────────────────
  if (
    lower.includes("not rera") ||
    lower.includes("no rera") ||
    lower.includes("unregistered")
  ) {
    extracted.is_rera_registered = 0;
  } else {
    extracted.is_rera_registered = 1;
  }

  // ── Occupancy / Rental ────────────────────────────────────────────────
  if (
    lower.includes("rented") ||
    lower.includes("rental") ||
    lower.includes("tenant")
  ) {
    extracted.occupancy = "rented";
    const rentMatch = lower.match(
      /(\d+(?:\.\d+)?)\s*%?\s*(?:rental\s*yield|yield)/,
    );
    if (rentMatch) extracted.rental_yield_pct = parseFloat(rentMatch[1]);
    else extracted.rental_yield_pct = 3.2;
  } else if (lower.includes("vacant") || lower.includes("empty")) {
    extracted.occupancy = "vacant";
    extracted.rental_yield_pct = 0;
  } else {
    extracted.occupancy = "self_occupied";
    extracted.rental_yield_pct = 0;
  }

  return { extracted, missing };
}

// ── Chatbot conversation flow ──────────────────────────────────────────────

export function generateBotResponse(userText, currentForm, missingFields) {
  const lower = userText.toLowerCase();

  // Greetings
  if (lower.match(/^(hi|hello|hey|namaste|start)/)) {
    return {
      text: "Hello! I'm PropIQ, your AI collateral assessment assistant. 🏠\n\nTell me about the property you want to assess. You can say something like:\n\n*\"2BHK apartment in Baner, 850 sqft, 8 years old, 5th floor\"*\n\nOr fill in the form on the right and I'll run the assessment.",
      action: null,
    };
  }

  // Help
  if (
    lower.includes("help") ||
    lower.includes("how") ||
    lower.includes("what can")
  ) {
    return {
      text: "I can assess any residential or commercial property in Pune, Mumbai, or Bangalore for collateral value.\n\n**Just tell me:**\n- Property type (2BHK, villa, shop...)\n- Locality (Baner, Andheri, Koramangala...)\n- Size in sqft\n- Building age\n- Floor number\n- Freehold or leasehold?\n\n**I'll give you:**\n✓ Market value range\n✓ Distress sale value\n✓ Resale liquidity score\n✓ Risk flags\n✓ Downloadable PDF report",
      action: null,
    };
  }

  // Assessment trigger
  if (
    lower.includes("assess") ||
    lower.includes("value") ||
    lower.includes("valuat") ||
    lower.includes("how much") ||
    lower.includes("worth") ||
    lower.includes("price")
  ) {
    return {
      text: "Running the assessment now...",
      action: "ASSESS",
    };
  }

  // PDF
  if (
    lower.includes("pdf") ||
    lower.includes("report") ||
    lower.includes("download")
  ) {
    return {
      text: "Generating your RBI-ready PDF report...",
      action: "PDF",
    };
  }

  // Missing fields prompt
  if (missingFields && missingFields.length > 0) {
    const field = missingFields[0];
    const prompts = {
      locality:
        "Which locality is the property in? (e.g. Baner, Andheri, Koramangala)",
      "property type":
        "What type of property is it? (1BHK / 2BHK / 3BHK / villa / shop / plot)",
      "size in sqft": "What is the carpet/built-up area in sqft?",
      "building age":
        "How old is the building? (e.g. 5 years, built in 2015, new)",
    };
    return {
      text: prompts[field] || `Could you tell me the ${field}?`,
      action: null,
    };
  }

  // All fields filled
  if (
    currentForm &&
    currentForm.locality &&
    currentForm.prop_type &&
    currentForm.size_sqft &&
    currentForm.age_years !== undefined
  ) {
    return {
      text: `Got it! Assessing a **${currentForm.prop_type.replace(/_/g, " ").toUpperCase()}** in **${currentForm.locality}** (${currentForm.size_sqft} sqft, ${currentForm.age_years} yrs old).\n\nClick **Run Assessment** or say *"assess now"* to get the valuation.`,
      action: null,
    };
  }

  return {
    text: 'I didn\'t quite catch that. Try describing the property: type, locality, size, and age. For example:\n\n*"3BHK in Kothrud, 1100 sqft, 10 years old"*',
    action: null,
  };
}
