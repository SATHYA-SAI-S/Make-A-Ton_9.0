import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.notifications.models import Notification
from backend.app.shared.ports import NotificationPort

TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"])
)

SUBJECT_MAP = {
    "password_reset": "SubscriptIQ - Password Reset Request",
    "invoice_generated": "SubscriptIQ - New Invoice Generated",
    "invoice_confirmed": "SubscriptIQ - Invoice Confirmed",
    "due_reminder": "SubscriptIQ - Invoice Due Soon",
    "overdue_reminder_1": "SubscriptIQ - Payment Notice (Level 1)",
    "overdue_reminder_2": "SubscriptIQ - Urgent: Invoice Overdue (Level 2)",
    "overdue_reminder_3": "SubscriptIQ - Final Warning: Invoice Overdue (Level 3)",
    "payment_received": "SubscriptIQ - Payment Received",
    "payment_failed": "SubscriptIQ - Payment Failed",
    "renewal_confirmed": "SubscriptIQ - Subscription Renewed"
}

class NotificationService(NotificationPort):
    def __init__(self, smtp_host: str = None, smtp_port: int = None, mock_send: bool = False):
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.mock_send = mock_send

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        # Strip extension if passed
        name = template_name.replace(".html", "")
        tpl = jinja_env.get_template(f"{name}.html")
        return tpl.render(**context)

    def send(self, template: str, to: str, context: Dict[str, Any], customer_id: Optional[str] = None) -> bool:
        subject = context.get("subject") or SUBJECT_MAP.get(template, f"SubscriptIQ Notification: {template}")
        body_html = self.render(template, context)

        db = SessionLocal()
        notification = Notification(
            template=template,
            recipient=to,
            customer_id=customer_id,
            subject=subject,
            status="QUEUED",
            attempts=0
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Attempt sending with retries (up to 3 attempts)
        max_attempts = 3
        sent = False
        last_error = None

        for attempt in range(1, max_attempts + 1):
            notification.attempts = attempt
            try:
                if self.mock_send:
                    sent = True
                    break

                # Send via SMTP
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
                msg["To"] = to
                msg.attach(MIMEText(body_html, "html"))

                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

                sent = True
                break
            except Exception as e:
                last_error = str(e)

        if sent:
            notification.status = "SENT"
            notification.sent_at = datetime.now(timezone.utc)
            notification.error = None
        else:
            notification.status = "FAILED"
            notification.error = last_error

        db.commit()
        db.close()
        return sent
