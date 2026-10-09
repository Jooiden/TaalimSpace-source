import smtplib
import ssl
from email.message import EmailMessage
from app.config import get_settings


def check_available() -> None:
    """Check provider access for every reset request, before looking up the account."""
    s = get_settings()
    if not configured():
        raise RuntimeError("Mail is not configured")
    if s.brevo_api_key.get_secret_value():
        import httpx
        response = httpx.get("https://api.brevo.com/v3/account",
            headers={"api-key": s.brevo_api_key.get_secret_value()}, timeout=10)
        response.raise_for_status()


def configured() -> bool:
    s = get_settings()
    return bool((s.smtp_host or s.brevo_api_key.get_secret_value()) and s.smtp_from)


def send_email(to: str, subject: str, body: str) -> None:
    s = get_settings()
    if not configured():
        raise RuntimeError("Mail is not configured")
    if s.brevo_api_key.get_secret_value():
        import httpx
        response=httpx.post("https://api.brevo.com/v3/smtp/email",headers={"api-key":s.brevo_api_key.get_secret_value()},
            json={"sender":{"name":"TaalimSpace","email":s.smtp_from},"to":[{"email":to}],"subject":subject,"textContent":body},timeout=15)
        response.raise_for_status()
        return
    message = EmailMessage()
    message["From"] = s.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    if s.smtp_port == 465:
        client = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, timeout=15, context=ssl.create_default_context())
    else:
        client = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15)
        client.starttls(context=ssl.create_default_context())
    with client:
        if s.smtp_user:
            client.login(s.smtp_user, s.smtp_password.get_secret_value())
        client.send_message(message)
