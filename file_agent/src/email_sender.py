import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SUBJECT_PREFIX = "resumen archivo: "


class EmailConfigError(Exception):
    pass


class EmailSender:
    def __init__(self):
        self._host = os.getenv("SMTP_HOST", "")
        self._port = int(os.getenv("SMTP_PORT", "587"))
        self._user = os.getenv("SMTP_USER", "")
        self._password = os.getenv("SMTP_PASSWORD", "")
        self._to = os.getenv("EMAIL_TO", "")

    def is_configured(self) -> bool:
        return all([self._host, self._user, self._password, self._to])

    def send_summary(self, filename: str, summary: str) -> None:
        if not self.is_configured():
            raise EmailConfigError(
                "Faltan variables de entorno: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAIL_TO"
            )

        msg = MIMEMultipart()
        msg["From"] = self._user
        msg["To"] = self._to
        msg["Subject"] = f"{SUBJECT_PREFIX}{filename}"
        msg.attach(MIMEText(summary, "plain", "utf-8"))

        with smtplib.SMTP(self._host, self._port) as server:
            server.starttls()
            server.login(self._user, self._password)
            server.send_message(msg)
