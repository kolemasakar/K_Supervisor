import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid

from .email import OutboundEmail


@dataclass(frozen=True)
class SMTPRelaySettings:
    host: str
    sender_email: str
    port: int = 25
    use_starttls: bool = False
    timeout_seconds: float = 30.0


class SMTPRelayEmailProvider:
    def __init__(self, settings: SMTPRelaySettings):
        self.settings = settings

    def send(self, message: OutboundEmail, idempotency_key: str) -> str:
        email = EmailMessage()
        email["From"] = self.settings.sender_email
        email["To"] = message.recipient
        email["Subject"] = message.subject
        email["Message-ID"] = make_msgid()
        email["X-K-Supervisor-Idempotency-Key"] = idempotency_key
        email.set_content(message.body)

        with smtplib.SMTP(self.settings.host, self.settings.port, timeout=self.settings.timeout_seconds) as smtp:
            if self.settings.use_starttls:
                smtp.starttls(context=ssl.create_default_context())
            smtp.send_message(email)
        return str(email["Message-ID"])
