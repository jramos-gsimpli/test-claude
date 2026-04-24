import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List


class EmailNotificationError(Exception):
    pass


class EmailNotifier:
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password

    def send_notification(self, recipient: str, flights: List[Dict[str, Any]]) -> None:
        if not flights:
            return
        msg = self._build_email(recipient, flights)
        self._send(recipient, msg)

    def _build_email(self, recipient: str, flights: List[Dict[str, Any]]) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"Vuelos a Europa por menos de $870 USD - "
            f"{len(flights)} opcion(es) encontrada(s)"
        )
        msg["From"] = self._smtp_user
        msg["To"] = recipient
        msg.attach(MIMEText(self._format_body(flights), "plain"))
        return msg

    def _format_body(self, flights: List[Dict[str, Any]]) -> str:
        header = "Vuelos disponibles a Europa desde Buenos Aires:\n\n"
        entries = [
            (
                f"- {f['origin']} -> {f['destination']}\n"
                f"  Fecha de salida: {f['departure_at']}\n"
                f"  Precio: ${f['price']} {f['currency']}\n"
                f"  Aerolinea: {f['airline']}\n"
                f"  Escalas: {f['stops']}\n"
            )
            for f in sorted(flights, key=lambda x: x["price"])
        ]
        return header + "\n".join(entries)

    def _send(self, recipient: str, msg: MIMEMultipart) -> None:
        try:
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                server.login(self._smtp_user, self._smtp_password)
                server.sendmail(self._smtp_user, recipient, msg.as_string())
        except smtplib.SMTPException as e:
            raise EmailNotificationError(f"Failed to send email: {e}") from e
