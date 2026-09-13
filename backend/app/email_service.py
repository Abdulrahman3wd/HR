"""
email_service.py
=================
Sends transactional emails via Gmail SMTP (free tier). Currently used
for interview scheduling links. Uses Python's built-in smtplib — no
external dependency needed.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import SMTP_EMAIL, SMTP_APP_PASSWORD, SMTP_HOST, SMTP_PORT


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Returns True if the email was sent successfully, False otherwise.
    Never raises — scheduling should not fail just because the email
    couldn't be delivered (the HR can still copy the link manually).
    """
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        print("[WARNING] SMTP credentials not configured — email not sent.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False


def send_interview_scheduling_email(
    to_email: str,
    candidate_name: str,
    job_title: str,
    interview_type_label: str,
    booking_link: str,
) -> bool:
    subject = f"Schedule your {interview_type_label} — {job_title}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 24px; background: #F8FAFC; border-radius: 12px;">
        <h2 style="color: #0F172A;">Hello {candidate_name},</h2>
        <p style="color: #475569; line-height: 1.6;">
            You've been invited to schedule your <strong>{interview_type_label}</strong>
            for the <strong>{job_title}</strong> position.
        </p>
        <p style="color: #475569; line-height: 1.6;">
            Please click the link below to choose a time that works for you:
        </p>
        <a href="{booking_link}"
           style="display: inline-block; background: #0F172A; color: white; padding: 12px 24px;
                  border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 12px;">
            Choose Your Interview Time
        </a>
        <p style="color: #94A3B8; font-size: 12px; margin-top: 24px;">
            If the button doesn't work, copy this link: {booking_link}
        </p>
    </div>
    """

    return send_email(to_email, subject, html_body)