import resend
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import RESEND_API_KEY, FROM_EMAIL, FROM_NAME


def send_email(to: str, subject: str, html: str, plain: str) -> bool:
    if RESEND_API_KEY:
        return _send_via_resend(to, subject, html, plain)
    else:
        return _send_via_smtp(to, subject, html, plain)


def _send_via_resend(to: str, subject: str, html: str, plain: str) -> bool:
    resend.api_key = RESEND_API_KEY
    try:
        resend.Emails.send({
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": [to],
            "subject": subject,
            "html": html,
            "text": plain,
        })
        print(f"[email] Sent to {to} via Resend")
        return True
    except Exception as e:
        print(f"[email] Resend error for {to}: {e}")
        return False


def _send_via_smtp(to: str, subject: str, html: str, plain: str) -> bool:
    import os
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print(f"[email] SMTP not configured — would send to {to}")
        print(f"[email] Subject: {subject}")
        return True  # dry run success

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{FROM_NAME} <{smtp_user}>"
        msg["To"] = to
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to, msg.as_string())

        print(f"[email] Sent to {to} via SMTP")
        return True
    except Exception as e:
        print(f"[email] SMTP error for {to}: {e}")
        return False
