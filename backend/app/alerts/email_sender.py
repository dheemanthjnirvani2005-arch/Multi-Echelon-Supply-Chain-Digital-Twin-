# backend/app/alerts/email_sender.py
"""Async email sender using aiosmtplib with Jinja2 HTML templates."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template
from app.core.config import settings

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = """<!DOCTYPE html>
<html><head><style>
body { font-family: Arial, sans-serif; color: #333; }
.header { background: {{ header_color }}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
.body { background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }
.metric { font-size: 28px; font-weight: bold; color: {{ header_color }}; }
.footer { font-size: 12px; color: #999; margin-top: 20px; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
td { padding: 8px 12px; border-bottom: 1px solid #eee; }
td:first-child { font-weight: bold; color: #555; width: 140px; }
</style></head><body>
<div class="header">
  <h2 style="margin:0">🚨 SupplyChain-Twin Alert — {{ severity | upper }}</h2>
  <p style="margin:4px 0 0 0">{{ rule_name }}</p>
</div>
<div class="body">
  <p class="metric">{{ metric }}: {{ value }}</p>
  <table>
    <tr><td>Node</td><td>{{ node_id }}</td></tr>
    <tr><td>Metric</td><td>{{ metric }}</td></tr>
    <tr><td>Current Value</td><td>{{ value }}</td></tr>
    <tr><td>Threshold</td><td>{{ threshold }}</td></tr>
    <tr><td>Severity</td><td>{{ severity | upper }}</td></tr>
    <tr><td>Triggered At</td><td>{{ fired_at }}</td></tr>
  </table>
</div>
<div class="footer">SupplyChain-Twin | Automated Alert System</div>
</body></html>"""

SEVERITY_COLORS = {"info": "#2196F3", "warning": "#F57C00", "critical": "#C62828"}


async def send_alert_email(alert) -> bool:
    """Send an HTML alert email. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("Email not configured — skipping email notification")
        return False

    try:
        import aiosmtplib
    except ImportError:
        logger.warning("aiosmtplib not installed — skipping email")
        return False

    severity = alert.severity or "warning"
    color = SEVERITY_COLORS.get(severity, "#333")

    html = Template(EMAIL_TEMPLATE).render(
        severity=severity,
        rule_name=alert.message or "Threshold Breach",
        node_id=alert.node_id,
        metric=alert.metric,
        value=f"{alert.value:.2f}",
        threshold=f"{alert.threshold:.2f}",
        fired_at=str(getattr(alert, 'fired_at', 'now')),
        header_color=color,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{severity.upper()}] Supply Chain Alert: {alert.node_id} — {alert.metric}"
    msg["From"] = settings.ALERT_EMAIL_FROM
    msg["To"] = settings.ALERT_EMAIL_TO
    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=False,
            start_tls=True,
        )
        logger.info(f"📧 Alert email sent for alert #{alert.id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send alert email: {e}")
        return False
