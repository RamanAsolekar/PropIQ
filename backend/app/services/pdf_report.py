"""
PropIQ PDF Report Generator
Produces RBI-ready collateral assessment documents for LAP credit files.
Uses ReportLab — no external dependencies beyond requirements.txt
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from pathlib import Path
from datetime import datetime

# ── Brand colours ──────────────────────────────────────────────────────────
BRAND_PURPLE = colors.HexColor("#534AB7")
BRAND_TEAL   = colors.HexColor("#0F6E56")
LIGHT_GRAY   = colors.HexColor("#F1EFE8")
MID_GRAY     = colors.HexColor("#888780")
DARK         = colors.HexColor("#2C2C2A")
WHITE        = colors.white
FLAG_RED     = colors.HexColor("#A32D2D")
FLAG_AMBER   = colors.HexColor("#BA7517")
FLAG_GREEN   = colors.HexColor("#3B6D11")

def _fmt_inr(value: int) -> str:
    """Format number as Indian currency string."""
    if value >= 10_000_000:
        return f"₹{value/10_000_000:.2f} Cr"
    elif value >= 100_000:
        return f"₹{value/100_000:.2f} L"
    else:
        return f"₹{value:,}"

def _rpi_label(rpi: float) -> tuple:
    """Return (label, colour) for Resale Potential Index."""
    if rpi >= 75:
        return "Highly Liquid", FLAG_GREEN
    elif rpi >= 50:
        return "Moderate Liquidity", FLAG_AMBER
    else:
        return "Illiquid / Specialised", FLAG_RED

def _confidence_label(score: float) -> str:
    if score >= 0.80: return "High"
    elif score >= 0.60: return "Medium"
    else: return "Low"

def _severity_color(severity: str) -> colors.Color:
    return {"high": FLAG_RED, "medium": FLAG_AMBER, "low": MID_GRAY}.get(severity, MID_GRAY)


def generate_pdf_report(assessment: dict) -> bytes:
    """
    Generate a complete RBI-ready PDF collateral report.
    Returns PDF as bytes — ready to stream or save.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Custom styles ──────────────────────────────────────────────────────
    h1 = ParagraphStyle("h1", parent=styles["Normal"],
        fontSize=18, textColor=BRAND_PURPLE, fontName="Helvetica-Bold",
        spaceAfter=2*mm, leading=22)
    h2 = ParagraphStyle("h2", parent=styles["Normal"],
        fontSize=11, textColor=BRAND_PURPLE, fontName="Helvetica-Bold",
        spaceBefore=5*mm, spaceAfter=2*mm, leading=14)
    h3 = ParagraphStyle("h3", parent=styles["Normal"],
        fontSize=9, textColor=DARK, fontName="Helvetica-Bold",
        spaceAfter=1*mm, leading=12)
    body = ParagraphStyle("body", parent=styles["Normal"],
        fontSize=9, textColor=DARK, fontName="Helvetica",
        leading=13, spaceAfter=1*mm)
    small = ParagraphStyle("small", parent=styles["Normal"],
        fontSize=8, textColor=MID_GRAY, fontName="Helvetica", leading=11)
    center = ParagraphStyle("center", parent=body, alignment=TA_CENTER)
    right_gray = ParagraphStyle("rg", parent=small, alignment=TA_RIGHT)

    # ── HEADER ─────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("<b>PropIQ</b>", ParagraphStyle("logo", parent=h1,
            fontSize=22, textColor=BRAND_PURPLE)),
        Paragraph(
            f"<b>Collateral Assessment Report</b><br/>"
            f"<font color='#888780' size='8'>Request ID: {assessment.get('request_id','—')} &nbsp;|&nbsp; "
            f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}</font>",
            ParagraphStyle("hdr_right", parent=body, alignment=TA_RIGHT)
        ),
    ]]
    header_table = Table(header_data, colWidths=["40%", "60%"])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3*mm),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_PURPLE, spaceAfter=4*mm))

    # ── PROPERTY DETAILS ───────────────────────────────────────────────────
    story.append(Paragraph("Property Details", h2))
    enrichment = assessment.get("enrichment", {})
    prop_rows = [
        ["Locality", assessment.get("locality","—"), "Zone Tier", enrichment.get("zone_tier","—").title()],
        ["Property Type", assessment.get("prop_type","—").replace("_"," ").title(),
         "Size", f"{assessment.get('size_sqft',0):,.0f} sqft"],
        ["Circle Rate", f"₹{enrichment.get('circle_rate_per_sqft',0):,}/sqft",
         "Infra Score", f"{enrichment.get('infra_score',0):.0f}/100"],
        ["Listing Density", f"{enrichment.get('listing_density',0):.0%}",
         "Model MAPE", f"{assessment.get('model_mape_pct','—')}%"],
    ]
    pt = Table(prop_rows, colWidths=["22%", "28%", "22%", "28%"])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), LIGHT_GRAY),
        ("BACKGROUND", (2,0), (2,-1), LIGHT_GRAY),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (-1,-1), DARK),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, colors.HexColor("#FAFAF8")]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D3D1C7")),
        ("PADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(pt)
    story.append(Spacer(1, 4*mm))

    # ── VALUATION SUMMARY ──────────────────────────────────────────────────
    story.append(Paragraph("Valuation Summary", h2))
    mv = assessment.get("market_value_range", [0, 0])
    dv = assessment.get("distress_value_range", [0, 0])
    mv_mid = assessment.get("market_value_mid", 0)
    rpi = assessment.get("resale_potential_index", 0)
    rpi_label, rpi_color = _rpi_label(rpi)
    conf = assessment.get("confidence_score", 0)
    ttl = assessment.get("estimated_time_to_sell_days", [0, 0])

    val_data = [
        ["METRIC", "VALUE", "RANGE / NOTES"],
        ["Market Value (Estimated)",
         Paragraph(f"<b>{_fmt_inr(mv_mid)}</b>", ParagraphStyle("vb", parent=body, textColor=BRAND_TEAL, fontSize=11)),
         f"{_fmt_inr(mv[0])}  –  {_fmt_inr(mv[1])}"],
        ["Distress Sale Value",
         Paragraph(f"<b>{_fmt_inr(int((dv[0]+dv[1])/2))}</b>", ParagraphStyle("vb2", parent=body, textColor=FLAG_AMBER, fontSize=11)),
         f"{_fmt_inr(dv[0])}  –  {_fmt_inr(dv[1])}"],
        ["Price per Sqft", f"₹{assessment.get('price_per_sqft_estimate',0):,}/sqft", "P50 estimate"],
        ["Resale Potential Index",
         Paragraph(f"<b>{rpi:.1f}/100</b>", ParagraphStyle("rpi", parent=body, textColor=rpi_color, fontSize=11)),
         rpi_label],
        ["Time to Liquidate", f"{ttl[0]}–{ttl[1]} days", "Expected market absorption"],
        ["Confidence Score",
         Paragraph(f"<b>{conf:.0%}</b>", ParagraphStyle("conf", parent=body,
             textColor=FLAG_GREEN if conf >= 0.8 else FLAG_AMBER, fontSize=11)),
         _confidence_label(conf)],
    ]
    vt = Table(val_data, colWidths=["38%", "28%", "34%"])
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_PURPLE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, colors.HexColor("#F7F7F4")]),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("TEXTCOLOR", (0,1), (0,-1), DARK),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D3D1C7")),
        ("PADDING", (0,0), (-1,-1), 5),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(vt)
    story.append(Spacer(1, 4*mm))

    # ── KEY VALUE DRIVERS (SHAP) ───────────────────────────────────────────
    drivers = assessment.get("key_drivers", [])
    if drivers:
        story.append(Paragraph("Key Value Drivers (SHAP Analysis)", h2))
        story.append(Paragraph(
            "SHAP (SHapley Additive exPlanations) values show how each feature contributed to the final valuation.",
            small))
        story.append(Spacer(1, 2*mm))
        driver_rows = [["FEATURE", "IMPACT (₹)", "DIRECTION"]]
        for d in drivers[:6]:
            feat_name = d.get("feature","").replace("_"," ").title()
            impact = d.get("impact_inr", 0)
            direction = d.get("direction","neutral")
            color_str = "#3B6D11" if direction == "positive" else "#A32D2D"
            sign = "+" if direction == "positive" else "–"
            driver_rows.append([
                feat_name,
                Paragraph(f"<b><font color='{color_str}'>{sign} {_fmt_inr(abs(impact))}</font></b>",
                    ParagraphStyle("di", parent=body)),
                direction.title(),
            ])
        dt = Table(driver_rows, colWidths=["45%", "30%", "25%"])
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), BRAND_TEAL),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, colors.HexColor("#F7F7F4")]),
            ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D3D1C7")),
            ("PADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(dt)
        story.append(Spacer(1, 4*mm))

    # ── RISK FLAGS ─────────────────────────────────────────────────────────
    story.append(Paragraph("Risk Flags & Compliance Checks", h2))
    flags = assessment.get("risk_flags", [])
    if not flags:
        story.append(Paragraph(
            "<font color='#3B6D11'>✓ No risk flags detected. Property inputs pass all automated checks.</font>",
            ParagraphStyle("ok", parent=body, textColor=FLAG_GREEN)))
    else:
        flag_rows = [["SEVERITY", "FLAG", "DETAIL"]]
        for f in flags:
            sev = f.get("severity","low")
            sev_color = _severity_color(sev)
            flag_rows.append([
                Paragraph(f"<b>{sev.upper()}</b>",
                    ParagraphStyle("sev", parent=body, textColor=sev_color)),
                f.get("flag","").replace("_"," ").title(),
                f.get("detail",""),
            ])
        ft = Table(flag_rows, colWidths=["15%", "30%", "55%"])
        ft.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), FLAG_RED),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#FFF5F5"), WHITE]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#F09595")),
            ("PADDING", (0,0), (-1,-1), 4),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story.append(ft)
    story.append(Spacer(1, 4*mm))

    # ── CV ASSESSMENT (if present) ─────────────────────────────────────────
    cv = assessment.get("cv_assessment")
    if cv and cv.get("image_analyzed"):
        story.append(Paragraph("Computer Vision — Property Condition Assessment", h2))
        condition = cv.get("condition","—").title()
        factor = cv.get("valuation_adjustment_factor", 1.0)
        adj_pct = (factor - 1.0) * 100
        adj_str = f"+{adj_pct:.0f}%" if adj_pct >= 0 else f"{adj_pct:.0f}%"
        adj_color = FLAG_GREEN if adj_pct > 0 else FLAG_RED if adj_pct < 0 else MID_GRAY
        cv_rows = [
            ["Detected Condition", condition],
            ["Quality Score", f"{cv.get('quality_score',0):.1f}/100"],
            ["Valuation Adjustment", Paragraph(f"<b><font color='#{adj_color.hexval()[1:]}'>{adj_str}</font></b>",
                ParagraphStyle("cv", parent=body))],
            ["CV Confidence", f"{cv.get('cv_confidence',0):.0%}"],
            ["Description", cv.get("adjustment_description","—")],
        ]
        cvt = Table(cv_rows, colWidths=["35%", "65%"])
        cvt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,-1), LIGHT_GRAY),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D3D1C7")),
            ("PADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(cvt)
        story.append(Spacer(1, 4*mm))

    # ── DISCLAIMER ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=3*mm))
    disclaimer = (
        "<b>Disclaimer:</b> This report is generated by PropIQ, an AI-assisted collateral valuation system. "
        "All values are estimates based on circle rate data (IGR Maharashtra 2024-25), OSM infrastructure data, "
        "and a machine learning model validated with MAPE of 8.3%. This report is intended as a decision-support "
        "tool for credit underwriting and does not replace a formal property valuation by a certified valuer. "
        "Lenders should exercise independent judgment. Model outputs are range-based to reflect inherent valuation uncertainty. "
        f"Generated by PropIQ v{assessment.get('version','1.0.0')} | {datetime.now().strftime('%d %b %Y')}"
    )
    story.append(Paragraph(disclaimer, small))

    doc.build(story)
    return buffer.getvalue()


if __name__ == "__main__":
    # Quick test
    sample = {
        "request_id": "A1B2C3D4",
        "locality": "Baner",
        "prop_type": "2bhk_apartment",
        "size_sqft": 850,
        "market_value_range": [17200000, 20800000],
        "market_value_mid": 19000000,
        "distress_value_range": [14276000, 17264000],
        "resale_potential_index": 85.2,
        "estimated_time_to_sell_days": [25, 60],
        "confidence_score": 0.87,
        "price_per_sqft_estimate": 22353,
        "model_mape_pct": 8.3,
        "key_drivers": [
            {"feature": "circle_rate_per_sqft", "impact_inr": 4200000, "direction": "positive"},
            {"feature": "infra_score", "impact_inr": 1800000, "direction": "positive"},
            {"feature": "age_years", "impact_inr": -600000, "direction": "negative"},
            {"feature": "is_standard_config", "impact_inr": 900000, "direction": "positive"},
            {"feature": "listing_density", "impact_inr": 400000, "direction": "positive"},
        ],
        "risk_flags": [
            {"flag": "moderate_building_age", "severity": "low", "detail": "Building is 8 years old — minor depreciation applied."}
        ],
        "enrichment": {
            "zone_tier": "prime",
            "circle_rate_per_sqft": 10800,
            "infra_score": 72.0,
            "listing_density": 0.811,
            "geo": {"lat": 18.559, "lon": 73.7868},
        },
        "cv_assessment": None,
        "version": "1.0.0",
    }
    pdf_bytes = generate_pdf_report(sample)
    out = Path("test_report.pdf")
    out.write_bytes(pdf_bytes)
    print(f"PDF generated: {out} ({len(pdf_bytes)//1024} KB)")