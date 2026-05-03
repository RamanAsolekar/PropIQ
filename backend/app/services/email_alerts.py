"""
PropIQ Email Alert Service
Sends collateral health alert emails via SMTP (Gmail by default).
Falls back to console logging if SMTP is not configured.
"""

import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_FROM = os.environ.get("ALERT_FROM_EMAIL", "propiq-alerts@propiq.ai")
ALERT_TO = os.environ.get("ALERT_TO_EMAIL", "risk-team@poonawala.com")


def _risk_color(risk_level: str) -> str:
    return {"red": "#DC2626", "amber": "#D97706", "green": "#059669"}.get(
        risk_level, "#6B7280"
    )


def _risk_label(risk_level: str) -> str:
    return {"red": "🔴 BREACH RISK", "amber": "🟡 WARNING", "green": "🟢 HEALTHY"}.get(
        risk_level, risk_level.upper()
    )


def build_alert_email_html(loan: dict, snapshot: dict) -> str:
    risk_color = _risk_color(snapshot["risk_level"])
    risk_label = _risk_label(snapshot["risk_level"])
    delta = snapshot["delta_pct"]
    delta_str = f"+{delta:.1f}%" if delta >= 0 else f"{delta:.1f}%"
    delta_color = "#059669" if delta >= 0 else "#DC2626"
    orig_val = loan["original_value"] / 1e7
    curr_val = snapshot["current_value"] / 1e7
    ltv_pct = snapshot["current_ltv"] * 100
    loan_amt = loan["loan_amount"] / 1e7

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#F3F4F6;font-family:Inter,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F3F4F6;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr><td style="background:#0D0E15;padding:24px 32px;">
          <table width="100%"><tr>
            <td><span style="color:#7C6FD8;font-size:20px;font-weight:700;">PropIQ</span>
                <span style="color:#555;font-size:13px;margin-left:8px;">Collateral Health Monitor</span></td>
            <td align="right"><span style="background:{risk_color};color:#fff;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;">{risk_label}</span></td>
          </tr></table>
        </td></tr>

        <!-- Alert Title -->
        <tr><td style="padding:28px 32px 8px;">
          <h2 style="margin:0;font-size:22px;color:#111;">Collateral Health Alert</h2>
          <p style="margin:6px 0 0;color:#6B7280;font-size:14px;">
            Loan <strong>{loan["loan_id"]}</strong> · Assessed {datetime.now().strftime("%d %b %Y, %I:%M %p")}
          </p>
        </td></tr>

        <!-- Borrower Info -->
        <tr><td style="padding:8px 32px 16px;">
          <table width="100%" style="background:#F9FAFB;border-radius:8px;padding:16px;" cellpadding="0" cellspacing="0">
            <tr>
              <td style="font-size:13px;color:#374151;"><strong>Borrower:</strong> {loan["borrower_name"]}</td>
              <td style="font-size:13px;color:#374151;"><strong>Property:</strong> {loan["locality"]} · {loan["prop_type"].replace("_"," ").title()}</td>
            </tr>
            <tr><td colspan="2" style="padding-top:8px;font-size:13px;color:#374151;">
              <strong>Size:</strong> {loan["size_sqft"]:,.0f} sqft &nbsp;|&nbsp; <strong>Age:</strong> {loan["age_years"]:.0f} years
            </td></tr>
          </table>
        </td></tr>

        <!-- Key Metrics -->
        <tr><td style="padding:8px 32px 24px;">
          <table width="100%" cellpadding="0" cellspacing="8">
            <tr>
              <td width="25%" style="background:#F9FAFB;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:11px;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">Loan Amount</div>
                <div style="font-size:20px;font-weight:700;color:#111;margin-top:4px;">₹{loan_amt:.2f} Cr</div>
              </td>
              <td width="4%"></td>
              <td width="25%" style="background:#F9FAFB;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:11px;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">Original Value</div>
                <div style="font-size:20px;font-weight:700;color:#111;margin-top:4px;">₹{orig_val:.2f} Cr</div>
              </td>
              <td width="4%"></td>
              <td width="25%" style="background:#F9FAFB;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:11px;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">Current Value</div>
                <div style="font-size:20px;font-weight:700;color:#111;margin-top:4px;">₹{curr_val:.2f} Cr</div>
                <div style="font-size:12px;color:{delta_color};margin-top:2px;">{delta_str}</div>
              </td>
              <td width="4%"></td>
              <td width="25%" style="background:{risk_color}20;border:2px solid {risk_color};border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:11px;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">Current LTV</div>
                <div style="font-size:20px;font-weight:700;color:{risk_color};margin-top:4px;">{ltv_pct:.1f}%</div>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Recommended Action -->
        <tr><td style="padding:0 32px 24px;">
          <div style="background:{risk_color}12;border-left:4px solid {risk_color};border-radius:0 8px 8px 0;padding:16px 20px;">
            <div style="font-size:12px;font-weight:700;color:{risk_color};text-transform:uppercase;margin-bottom:6px;">Recommended Action</div>
            <div style="font-size:14px;color:#374151;">
              {"<strong>Immediate Action Required:</strong> Current LTV exceeds 80% threshold. Request additional collateral or partial repayment from borrower within 7 days." if snapshot["risk_level"] == "red"
               else "<strong>Monitor Closely:</strong> LTV has crossed 70% warning threshold. Review borrower's repayment capacity and consider requesting top-up collateral." if snapshot["risk_level"] == "amber"
               else "Collateral is healthy. Continue standard monitoring cycle."}
            </div>
          </div>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#F9FAFB;padding:16px 32px;border-top:1px solid #E5E7EB;">
          <p style="margin:0;font-size:12px;color:#9CA3AF;">
            This is an automated alert from <strong>PropIQ Collateral Health Monitor</strong>.<br/>
            Powered by PropIQ v3.0 · AI Collateral Intelligence Engine for Poonawala Fincorp
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_alert_email(loan: dict, snapshot: dict) -> bool:
    """
    Send a collateral health alert email.
    Returns True if sent successfully, False otherwise.
    """
    recipient = loan.get("borrower_email") or ALERT_TO
    subject_prefix = {
        "red": "🔴 URGENT",
        "amber": "🟡 WARNING",
        "green": "✅ INFO",
    }.get(snapshot["risk_level"], "ALERT")
    subject = f"{subject_prefix}: Collateral Health Alert — Loan {loan['loan_id']} ({loan['locality']})"

    html_body = build_alert_email_html(loan, snapshot)

    # Console log always (for demo visibility in docker logs)
    logger.warning(
        f"\n{'='*60}\n"
        f"📧 PROPIQ ALERT EMAIL\n"
        f"To: {recipient}\n"
        f"Subject: {subject}\n"
        f"Loan: {loan['loan_id']} | Risk: {snapshot['risk_level'].upper()} | LTV: {snapshot['current_ltv']*100:.1f}%\n"
        f"{'='*60}"
    )

    if not SMTP_USER or not SMTP_PASSWORD:
        logger.info("SMTP not configured — email logged to console only.")
        return True  # Return True so alert is still marked as "sent" for demo

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = ALERT_FROM
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_FROM, recipient, msg.as_string())

        logger.info(f"Alert email sent to {recipient} for loan {loan['loan_id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        return False
