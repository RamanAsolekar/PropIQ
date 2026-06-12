"""
PropIQ LLM Narration Service
Uses Groq API (llama-3.3-70b) to convert JSON assessment into credit memo language.
This is the feature that makes PropIQ demo-ready — a loan officer
can read this output directly into a file note.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ensure .env is loaded from project root
from dotenv import load_dotenv

_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env", override=False)
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=False)

GROQ_MODEL = "llama-3.3-70b-versatile"


def fmt_inr(value: int) -> str:
    if value >= 10_000_000:
        return f"₹{value/10_000_000:.2f} Cr"
    if value >= 100_000:
        return f"₹{value/100_000:.2f} L"
    return f"₹{value:,}"


async def generate_credit_memo(assessment: dict) -> dict:
    """
    Generate a plain-English credit memo from assessment JSON using Groq.
    Returns: { summary, recommendation, risk_narrative, key_points }
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return _fallback_memo(assessment)

    mv = assessment.get("market_value_range", [0, 0])
    dv = assessment.get("distress_value_range", [0, 0])
    rpi = assessment.get("resale_potential_index", 0)
    conf = assessment.get("confidence_score", 0)
    flags = assessment.get("risk_flags", [])
    drivers = assessment.get("key_drivers", [])
    enrichment = assessment.get("enrichment", {})

    # ── RAG grounding: retrieve relevant RBI / internal-policy snippets ──────
    grounding_block = ""
    citations = []
    try:
        from app.services.rag import build_grounding_block, retrieve_context

        zone = enrichment.get("zone_tier", "")
        ptype = assessment.get("prop_type", "").replace("_", " ")
        rag_query = (
            f"LAP LTV norms and credit policy for a {ptype} in a {zone} zone, "
            f"market value {assessment.get('market_value_mid', 0)}, "
            f"resale potential {rpi}, risk flags {len(flags)}"
        )
        snippets = retrieve_context(rag_query)
        grounding_block = build_grounding_block(snippets)
        citations = [s["citation"] for s in snippets]
    except Exception as _e:
        print(f"[memo] RAG grounding skipped (non-fatal): {_e}")

    prompt = f"""You are a senior credit analyst at Poonawalla Fincorp writing a collateral file note for a LAP (Loan Against Property) application.

Based on the following PropIQ AI assessment, write a concise professional credit memo. Use plain English. Be specific with numbers. Sound like an experienced banker, not an AI.
{('Ground every regulatory/policy claim in the POLICY CONTEXT below and cite the [source] tag inline.' + chr(10) + grounding_block) if grounding_block else ''}

ASSESSMENT DATA:
- Property: {assessment.get('prop_type','').replace('_',' ').title()} in {assessment.get('locality','')}, Pune
- Size: {assessment.get('size_sqft',0):,} sqft
- Market Value Range: {fmt_inr(mv[0])} – {fmt_inr(mv[1])} (mid: {fmt_inr(assessment.get('market_value_mid',0))})
- Distress Value: {fmt_inr(dv[0])} – {fmt_inr(dv[1])}
- Resale Potential Index: {rpi}/100 ({'Highly Liquid' if rpi>=75 else 'Moderate' if rpi>=50 else 'Illiquid'})
- Time to Liquidate: {assessment.get('estimated_time_to_sell_days',['?','?'])[0]}–{assessment.get('estimated_time_to_sell_days',['?','?'])[1]} days
- Confidence Score: {conf:.0%}
- Zone: {enrichment.get('zone_tier','').title()} | Circle Rate: ₹{enrichment.get('circle_rate_per_sqft',0):,}/sqft
- Infra Score: {enrichment.get('infra_score',0):.0f}/100
- Risk Flags: {len(flags)} ({'none' if not flags else ', '.join(f['flag'].replace('_',' ') for f in flags[:3])})
- Top Value Drivers: {', '.join(d['feature'].replace('_',' ') for d in drivers[:3])}
- CV Condition: {assessment.get('cv_assessment',{}).get('condition','not assessed') if assessment.get('cv_assessment') else 'not assessed'}

Write EXACTLY this JSON structure (no markdown, no preamble):
{{
  "summary": "2-3 sentence summary of the collateral suitable for a credit committee presentation",
  "recommendation": "One clear recommendation sentence: acceptable/marginal/unacceptable collateral and suggested LTV",
  "risk_narrative": "2-3 sentences on the key risks specific to this property",
  "key_points": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"]
}}"""

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=api_key)
        completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3,
        )
        text = completion.choices[0].message.content.strip()
        # Strip any accidental markdown fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        memo = json.loads(text)
        # Surface the policy sources the memo was grounded in (RAG provenance)
        if citations:
            memo["policy_citations"] = sorted(set(citations))
            memo["grounded"] = True
        return memo
    except Exception as e:
        print(f"LLM narration failed: {e} — using fallback")
        memo = _fallback_memo(assessment)
        if citations:
            memo["policy_citations"] = sorted(set(citations))
        return memo


async def stream_credit_memo(assessment: dict):
    """
    Async generator yielding credit-memo text deltas for SSE streaming.
    Falls back to yielding the deterministic memo in chunks if no LLM.
    """
    from app.services import llm_provider

    mv = assessment.get("market_value_range", [0, 0])
    rpi = assessment.get("resale_potential_index", 0)
    flags = assessment.get("risk_flags", [])
    prompt = (
        "Write a concise professional LAP collateral credit memo (plain English, "
        "experienced banker tone) for: "
        f"{assessment.get('prop_type','').replace('_',' ').title()} in "
        f"{assessment.get('locality','')}. Market value {fmt_inr(mv[0])}–{fmt_inr(mv[1])}, "
        f"RPI {rpi}/100, {len(flags)} risk flag(s). Cover summary, recommendation, "
        "key risks. 4-6 sentences."
    )
    if llm_provider.is_available():
        yield {"event": "start", "mode": "llm"}
        async for delta in llm_provider.chat_stream(
            [{"role": "user", "content": prompt}], model_tier="reason", max_tokens=400
        ):
            yield {"event": "token", "text": delta}
        yield {"event": "done"}
    else:
        memo = _fallback_memo(assessment)
        yield {"event": "start", "mode": "fallback"}
        for part in [memo["summary"], " ", memo["recommendation"], " ",
                     memo["risk_narrative"]]:
            yield {"event": "token", "text": part}
        yield {"event": "done"}


def _fallback_memo(assessment: dict) -> dict:
    """Deterministic fallback when API key not set."""
    mv = assessment.get("market_value_range", [0, 0])
    rpi = assessment.get("resale_potential_index", 0)
    flags = assessment.get("risk_flags", [])
    locality = assessment.get("locality", "the subject locality")
    prop_type = assessment.get("prop_type", "property").replace("_", " ")

    liq_label = (
        "highly liquid"
        if rpi >= 75
        else "moderately liquid" if rpi >= 50 else "relatively illiquid"
    )
    ltv = (
        "up to 65%"
        if rpi >= 75 and not flags
        else "up to 55%" if rpi >= 50 else "up to 45%"
    )
    flag_note = (
        (
            f"The assessment flagged {len(flags)} concern(s): "
            + ", ".join(f["flag"].replace("_", " ") for f in flags[:2])
            + "."
        )
        if flags
        else "No automated risk flags were detected."
    )

    return {
        "summary": (
            f"The subject property is a {prop_type} located in {locality}, Pune, "
            f"with an estimated market value range of {fmt_inr(mv[0])} to {fmt_inr(mv[1])}. "
            f"The asset is considered {liq_label} with a Resale Potential Index of {rpi:.0f}/100, "
            f"supported by infrastructure proximity and locality demand signals."
        ),
        "recommendation": (
            f"Collateral is {'acceptable' if rpi >= 50 and len(flags) == 0 else 'marginally acceptable'} "
            f"for LAP underwriting. Recommended maximum LTV: {ltv}. "
            f"{'Full title search and physical verification recommended before sanction.' if flags else 'Standard due diligence applies.'}"
        ),
        "risk_narrative": (
            f"{flag_note} "
            f"Liquidity risk is {'low' if rpi >= 75 else 'moderate' if rpi >= 50 else 'elevated'}, "
            f"with estimated time to liquidate of "
            f"{assessment.get('estimated_time_to_sell_days', [60,120])[0]}–"
            f"{assessment.get('estimated_time_to_sell_days', [60,120])[1]} days under normal market conditions."
        ),
        "key_points": [
            f"Market value range: {fmt_inr(mv[0])} – {fmt_inr(mv[1])} (AI model MAPE: {assessment.get('model_mape_pct','8.3')}%)",
            f"Resale Potential Index: {rpi:.0f}/100 — {liq_label}",
            f"Circle rate floor: ₹{assessment.get('enrichment',{}).get('circle_rate_per_sqft',0):,}/sqft (IGR Maharashtra 2024-25)",
            f"Risk flags: {len(flags)} detected — {'review required' if flags else 'clear'}",
        ],
    }


async def generate_risk_escalation_alert(assessment: dict) -> str:
    """
    Generate a professional 'Internal Risk Escalation Alert' using Groq
    when a stress test pushes a loan underwater (LTV > 100%).
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return f"INTERNAL MEMO\n\nTo: Credit Risk Committee\nSubject: Critical LTV Breach - {assessment.get('loan_id')}\n\nDue to severe market volatility, the collateral for loan {assessment.get('loan_id')} (Borrower: {assessment.get('borrower_name')}) has fallen significantly. The current stressed Loan-to-Value (LTV) ratio is {assessment.get('stressed_ltv', 0)*100:.1f}%. Immediate portfolio review and heightened monitoring recommended."

    prompt = f"""You are an automated Risk Management AI at Poonawalla Fincorp.
Write a concise, professional "Internal Risk Escalation Memo" addressed to the Credit Risk Committee regarding a Loan Against Property (LAP) that has just become critically unsecured due to a simulated macro-economic market shock.

LOAN DETAILS:
- Borrower: {assessment.get('borrower_name')}
- Loan ID: {assessment.get('loan_id')}
- Property: {assessment.get('prop_type', '').replace('_', ' ').title()} in {assessment.get('locality')}
- Outstanding Principal: ₹{assessment.get('loan_amount'):,}
- Original Collateral Value: ₹{assessment.get('original_value'):,}
- Current Stressed Collateral Value: ₹{assessment.get('stressed_value'):,} (Down {assessment.get('delta_pct'):.1f}%)
- Current LTV: {assessment.get('stressed_ltv')*100:.1f}% (Severe Breach of internal limits)

REQUIREMENT:
Draft the internal memo highlighting the vulnerability. Recommend actions such as blocking any top-up loans, increasing EMI monitoring, and tagging the account for high-risk provisioning. Do NOT ask the borrower for more collateral (as this is retail LAP in India). 

Return ONLY the memo body text (no JSON, no intro). Keep it under 150 words."""

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=api_key)
        completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.2,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Risk alert generation failed: {e}")
        return f"INTERNAL ALERT: Collateral value for {assessment.get('loan_id')} has fallen to ₹{assessment.get('stressed_value'):,}, pushing LTV to {assessment.get('stressed_ltv')*100:.1f}%. Tag for immediate monitoring."


async def generate_customer_letter(assessment: dict) -> str:
    """
    Generate a polite, plain-English "Customer-Facing Explainability Report"
    translating SHAP values and risk flags into a letter the borrower can understand.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return _fallback_customer_letter(assessment)

    mv = assessment.get("market_value_range", [0, 0])
    conf = assessment.get("confidence_score", 0)
    flags = assessment.get("risk_flags", [])
    drivers = assessment.get("key_drivers", [])

    prompt = f"""You are an automated assistant at Poonawalla Fincorp writing a letter to a customer who has applied for a Loan Against Property.

Write a polite, professional, and easy-to-understand letter explaining the valuation of their property. 

ASSESSMENT DATA:
- Property: {assessment.get('prop_type','').replace('_',' ').title()} in {assessment.get('locality','')}
- Estimated Market Value Range: {fmt_inr(mv[0])} – {fmt_inr(mv[1])} (mid: {fmt_inr(assessment.get('market_value_mid',0))})
- Key Positives/Negatives (from AI SHAP model): {', '.join([f"{d['feature'].replace('_',' ')} ({d['direction']})" for d in drivers[:4]])}
- Any noted issues (Risk Flags): {len(flags)} issues found ({', '.join([f['flag'].replace('_',' ') for f in flags[:2]]) if flags else 'None'})

REQUIREMENTS:
1. Address the customer politely (e.g. "Dear Valued Customer,").
2. State the estimated market value range clearly.
3. Explain the key factors (drivers) that positively or negatively influenced this value in simple, non-technical terms (do not use words like "SHAP" or "XGBoost").
4. If there are risk flags, mention them gently as areas that might require standard verification. If none, mention the property shows clear signals.
5. End with a professional sign-off from "Poonawalla Fincorp Collateral Assessment Team".
6. Return ONLY the letter text. No JSON, no markdown formatting blocks. Keep it to 3-4 paragraphs maximum."""

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=api_key)
        completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Customer letter generation failed: {e}")
        return _fallback_customer_letter(assessment)


def _fallback_customer_letter(assessment: dict) -> str:
    """Fallback customer letter if API fails or no key."""
    mv = assessment.get("market_value_range", [0, 0])
    drivers = assessment.get("key_drivers", [])
    flags = assessment.get("risk_flags", [])

    drivers_text = ""
    if drivers:
        positives = [
            d["feature"].replace("_", " ").title()
            for d in drivers
            if d["direction"] == "positive"
        ]
        negatives = [
            d["feature"].replace("_", " ").title()
            for d in drivers
            if d["direction"] == "negative"
        ]
        if positives:
            drivers_text += f"\n- Positively influenced by: {', '.join(positives[:3])}."
        if negatives:
            drivers_text += (
                f"\n- Areas slightly offsetting value: {', '.join(negatives[:2])}."
            )

    flags_text = "The assessment shows strong fundamental indicators with no major automated risk flags."
    if flags:
        flags_text = f"We noted a few areas that will require standard verification, such as: {flags[0]['flag'].replace('_',' ')}."

    return f"""Dear Valued Customer,

Thank you for choosing Poonawalla Fincorp for your Loan Against Property application. We have completed the preliminary automated assessment of your property in {assessment.get('locality', 'your area')}.

Based on current market data and comparable properties, the estimated market value of your property is between {fmt_inr(mv[0])} and {fmt_inr(mv[1])}. 

Our AI-driven analysis takes multiple local factors into account. For your property, the key factors influencing this valuation include:{drivers_text}

{flags_text} 

Please note this is an automated preliminary estimate. A final offer will be subject to our standard legal and technical due diligence.

Warm regards,
Poonawalla Fincorp Collateral Assessment Team"""
