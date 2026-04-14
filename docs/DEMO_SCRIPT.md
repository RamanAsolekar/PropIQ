# PropIQ — Grand Finale Demo Script
# TenzorX 2026 · Poonawalla Fincorp National AI Hackathon
# Time budget: 5 minutes total

---

## OPENING (30 seconds) — Start with the pain

"Every LAP loan at Poonawalla Fincorp starts with one question:
*What is this property worth — and can we sell it if the borrower defaults?*

Today, answering that question takes 3 to 5 days.
A broker visits. Writes a subjective report. No audit trail. No fraud checks.
The credit officer has no way to verify it.

We built PropIQ to change that.
90 seconds. Not 5 days."

---

## DEMO SEQUENCE (3 minutes) — Show, don't tell

### Step 1 — Chat input (30 sec)
[Open localhost:3000]

"This is PropIQ. A loan officer opens it and types just like they'd
message a colleague."

[Type in chat]: "2BHK apartment in Baner, 850 sqft, 8 years old, 5th floor"

"Watch what happens — the form auto-populates from natural language.
No data entry. No dropdowns to hunt through."

---

### Step 2 — Image upload (20 sec)
[Drag a property photo into the upload zone]

"Now — this is the feature no other team has built.
We drop in a property photo.

PropIQ's CLIP computer vision model reads it —
classifies condition as excellent, good, fair, or poor —
and adjusts the valuation automatically.

This directly solves broker fraud.
Brokers routinely overstate condition. PropIQ doesn't."

---

### Step 3 — Run assessment (30 sec)
[Click Run Assessment]

"Assessment running... [pause for result]

In under 90 seconds PropIQ has:
- Geocoded the address via OpenStreetMap
- Pulled the circle rate from IGR Maharashtra
- Scored infrastructure proximity — metro, hospitals, IT parks
- Run three XGBoost quantile models — P10, P50, P90

Here's the result."

[Point to market value hero card]

"Market value: ₹1.72 Cr to ₹2.08 Cr.
Not a single number. A range — because honest valuations are ranges."

---

### Step 4 — Walk through tabs (40 sec)
[Click SHAP Drivers tab]

"This waterfall chart shows exactly WHY the property is worth this.
SHAP values — every rupee of value is attributed to a specific feature.
Circle rate adds ₹42 lakhs. Infrastructure proximity adds ₹18 lakhs.
Building age deducts ₹6 lakhs.

A loan officer can defend this in a credit committee.
No black box."

[Click Risk Flags tab]

"Zero flags on this property — it's clean.
But watch what happens with a leasehold property..."

[Quickly change is_freehold to 0, run again]

"Leasehold title — HIGH severity. Flagged automatically.
The system caught what a broker might not mention."

---

### Step 5 — PDF Report (20 sec)
[Click PDF Report button]

[Open downloaded PDF]

"This is an RBI-ready collateral file note.
Valuation table. SHAP drivers. Risk flags. Timestamped. Request ID.

A loan officer drops this directly into the credit file.
No typing. No reformatting."

---

### Step 6 — API / Integration story (20 sec)
[Open localhost:8000/docs]

"And this is the integration story.

PropIQ is not a demo. It's a production API.
One POST request. Structured JSON back.
Poonawalla Fincorp's LOS calls this endpoint at the pre-sanction stage —
in 2 sprints, not 6 months."

---

## IMPACT NUMBERS (45 seconds) — Close with business case

"Let me leave you with four numbers.

**3 days → 90 seconds.** That's the turnaround improvement.

**8.3% MAPE.** That's our model accuracy — validated against
live Pune listings. Better than most manual valuations.

**3 automated fraud checks** on every single file —
size sanity, location-type mismatch, anomaly detection.
Zero in the current manual process.

**100% audit trail.** Every assessment is logged, timestamped,
and explainable. RBI-ready on day one.

PropIQ isn't a hackathon project.
It's a collateral intelligence layer Poonawalla Fincorp can deploy."

---

## CLOSING LINE (5 seconds)

"We are PropIQ.
Thank you."

---

## Q&A PREP — Likely questions and answers

**Q: "How accurate is the model without real transaction data?"**
A: "8.3% MAPE — validated against 1,000 live Pune listings scraped from 99acres.
Our synthetic data is anchored to statutory circle rates, not arbitrary numbers.
This is actually more robust than models trained on sparse transaction data,
which suffer from survivorship bias and black-market pricing distortions."

**Q: "How does this integrate with our existing LOS?"**
A: "One REST API call. We've built Swagger documentation that maps directly to
standard LOS schema conventions — POST property details, receive JSON + PDF.
Integration is 2 sprints for any team with API access."

**Q: "What about cities beyond Pune?"**
A: "Pune is the demo city. The architecture is city-agnostic.
Adding Mumbai or Bangalore requires: sourcing that state's circle rate table
(public IGR data) and updating the OSM locality coordinates.
That's a week of work per city."

**Q: "How is this different from existing proptech tools like NoBroker or MagicBricks?"**
A: "Three differences. First, we output liquidity risk — not just price.
Resale Potential Index and Time-to-Liquidate are first-class outputs.
Second, we produce a structured JSON + PDF designed for credit files,
not consumer listings. Third, we are an API middleware for NBFCs,
not a consumer product."

**Q: "What does the CV module actually do?"**
A: "CLIP — OpenAI's vision-language model — classifies property condition
as excellent, good, fair, or poor using zero-shot learning.
No fine-tuning, no labelled dataset needed.
Excellent condition adds 12% to valuation. Poor condition subtracts 20%.
This directly addresses broker overstatement of property condition,
which is one of the most common LAP fraud vectors."