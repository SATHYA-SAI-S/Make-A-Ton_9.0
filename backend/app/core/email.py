import os
import smtplib
import socket
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.errors import ValidationException

logger = logging.getLogger("subscriptiq.email")

# In-memory mailbox for automated tests
mock_sent_emails: List[Dict[str, Any]] = []


def clear_mock_mailbox() -> None:
    """Clear captured test emails."""
    mock_sent_emails.clear()


def get_mock_sent_emails() -> List[Dict[str, Any]]:
    """Retrieve captured test emails."""
    return list(mock_sent_emails)


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str
) -> bool:
    """
    Send an email via SMTP or record to mock provider during tests.
    Raises ValidationException if delivery fails or provider is unconfigured.
    """
    is_testing = bool(os.environ.get("PYTEST_CURRENT_TEST")) or settings.EMAIL_PROVIDER == "mock"

    if is_testing:
        mock_sent_emails.append({
            "to": to_email,
            "subject": subject,
            "html": html_content,
            "text": text_content,
        })
        logger.info(f"[Test Mailbox] Captured email to: {to_email} | Subject: {subject}")
        return True

    # Validate SMTP configuration
    if not settings.SMTP_HOST:
        raise ValidationException(
            message=(
                "Email delivery service is not configured. Please set SMTP_HOST and SMTP_PORT "
                "in backend/.env (e.g., SMTP_HOST=127.0.0.1, SMTP_PORT=1025 for Mailpit) to send genuine emails."
            ),
            code="EMAIL_SERVICE_NOT_CONFIGURED"
        )

    sender_identity = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_identity
    msg["To"] = to_email

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)

        with server:
            if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
                server.starttls()

            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())

        logger.info(f"Email successfully dispatched to: {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failure with configured credentials.")
        raise ValidationException(
            message="SMTP Authentication failed. Please check your SMTP username and password in backend/.env.",
            code="SMTP_AUTH_ERROR"
        )
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"Recipient address rejected: {to_email}")
        raise ValidationException(
            message=f"Recipient address '{to_email}' was rejected by the mail server.",
            code="EMAIL_RECIPIENT_REJECTED"
        )
    except (smtplib.SMTPException, socket.error, TimeoutError) as e:
        logger.error(f"SMTP delivery error to {to_email}: {type(e).__name__}")
        raise ValidationException(
            message=f"Failed to deliver email through SMTP server ({type(e).__name__}). Please verify host and network settings.",
            code="EMAIL_DELIVERY_FAILED"
        )


def send_registration_otp_email(to_email: str, recipient_name: str, otp: str) -> bool:
    """Send branded registration verification code email."""
    subject = "Verify Your SubscriptIQ Account"

    text_content = f"""Hello {recipient_name},

Thank you for registering with SubscriptIQ.

Your email verification code is:

{otp}

This code expires in 10 minutes and can only be used once.

If you did not initiate this registration, please ignore this email.

Regards,
SubscriptIQ Team
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .brand {{ display: flex; align-items: center; gap: 8px; font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 24px; }}
    .badge {{ background: #10b981; color: white; width: 32px; height: 32px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 8px; }}
    .otp-card {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0; }}
    .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #047857; font-family: Courier, monospace; }}
    .footer {{ font-size: 12px; color: #64748b; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="brand">
      <span class="badge">S</span> SubscriptIQ
    </div>
    <h2 style="color: #0f172a; margin-top: 0;">Verify Your Account</h2>
    <p>Hello <strong>{recipient_name}</strong>,</p>
    <p>Thank you for registering with SubscriptIQ. Please use the following single-use verification code to activate your customer account:</p>
    <div class="otp-card">
      <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #059669; margin-bottom: 6px;">Email Verification Code</div>
      <div class="otp-code">{otp}</div>
    </div>
    <p style="font-size: 13px; color: #475569;">
      ⏱️ This code expires in <strong>10 minutes</strong> and can only be used once.<br>
      🔒 For security, never share this verification code with anyone.
    </p>
    <p style="font-size: 13px; color: #64748b;">If you did not initiate this registration request, please ignore this email.</p>
    <div class="footer">
      &copy; 2026 SubscriptIQ Platform. All rights reserved.
    </div>
  </div>
</body>
</html>"""

    return send_email(to_email, subject, html_content, text_content)


def send_password_reset_otp_email(to_email: str, recipient_name: str, otp: str) -> bool:
    """Send branded password-reset verification code email."""
    subject = "Your SubscriptIQ Password Reset Code"

    text_content = f"""Hello {recipient_name},

We received a request to reset your SubscriptIQ account password.

Your password reset verification code is:

{otp}

This code expires in 10 minutes and can only be used once.

If you did not request a password reset, please ignore this email. Your existing password will remain unchanged.

Regards,
SubscriptIQ Team
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .brand {{ display: flex; align-items: center; gap: 8px; font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 24px; }}
    .badge {{ background: #10b981; color: white; width: 32px; height: 32px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 8px; }}
    .otp-card {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0; }}
    .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #1d4ed8; font-family: Courier, monospace; }}
    .footer {{ font-size: 12px; color: #64748b; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="brand">
      <span class="badge">S</span> SubscriptIQ
    </div>
    <h2 style="color: #0f172a; margin-top: 0;">Password Reset Request</h2>
    <p>Hello <strong>{recipient_name}</strong>,</p>
    <p>We received a request to reset your password. Use the verification code below to authorize your password update:</p>
    <div class="otp-card">
      <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #2563eb; margin-bottom: 6px;">Password Reset Code</div>
      <div class="otp-code">{otp}</div>
    </div>
    <p style="font-size: 13px; color: #475569;">
      ⏱️ This code expires in <strong>10 minutes</strong> and can only be used once.<br>
      🛡️ If you did not request a password reset, you can safely ignore this email.
    </p>
    <div class="footer">
      &copy; 2026 SubscriptIQ Platform. All rights reserved.
    </div>
  </div>
</body>
</html>"""

    return send_email(to_email, subject, html_content, text_content)
