import smtplib
from email.message import EmailMessage

from app import config


def send_email(to: str, subject: str, body: str) -> bool:
    """Sends one email. Returns True if it went out.
    In mock mode (the default) it only prints to the terminal."""
    if config.EMAIL_PROVIDER != "smtp":
        print(f"[MOCK EMAIL] to={to} | {subject}\n{body}", flush=True)
        return True
    try:
        msg = EmailMessage()
        msg["From"] = config.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as error:
        print("Email could not be sent:", error, flush=True)
        return False


def send_otp_email(to: str, code: str) -> bool:
    return send_email(
        to,
        "Your DearDoctor sign-in code",
        f"Your sign-in code is {code}. It expires in 5 minutes.\n"
        "If you did not try to sign in, you can ignore this email.",
    )