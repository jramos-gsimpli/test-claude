import smtplib
import pytest
from unittest.mock import MagicMock, patch
from src.email_notifier import EmailNotifier, EmailNotificationError


SMTP_CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "sender@example.com",
    "smtp_password": "secret",
}
RECIPIENT = "jramos@gruposimpli.com"


class TestEmailNotifier:
    @pytest.fixture(autouse=True)
    def setup(self, sample_flight):
        self.notifier = EmailNotifier(**SMTP_CONFIG)
        self.flight = sample_flight

    def _mock_smtp(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        return mock_server

    @patch("src.email_notifier.smtplib.SMTP")
    def test_sends_email_to_correct_recipient(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)

        self.notifier.send_notification(RECIPIENT, [self.flight])

        _, positional, _ = mock_server.sendmail.mock_calls[0]
        assert positional[1] == RECIPIENT

    @patch("src.email_notifier.smtplib.SMTP")
    def test_authenticates_with_configured_credentials(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)

        self.notifier.send_notification(RECIPIENT, [self.flight])

        mock_server.login.assert_called_once_with(
            SMTP_CONFIG["smtp_user"], SMTP_CONFIG["smtp_password"]
        )

    @patch("src.email_notifier.smtplib.SMTP")
    def test_uses_starttls_before_sending(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)

        self.notifier.send_notification(RECIPIENT, [self.flight])

        mock_server.starttls.assert_called_once()

    @patch("src.email_notifier.smtplib.SMTP")
    def test_connects_to_configured_smtp_host_and_port(self, mock_smtp_cls):
        self._mock_smtp(mock_smtp_cls)

        self.notifier.send_notification(RECIPIENT, [self.flight])

        mock_smtp_cls.assert_called_once_with(
            SMTP_CONFIG["smtp_host"], SMTP_CONFIG["smtp_port"]
        )

    @patch("src.email_notifier.smtplib.SMTP")
    def test_does_not_connect_when_flights_list_is_empty(self, mock_smtp_cls):
        self.notifier.send_notification(RECIPIENT, [])

        mock_smtp_cls.assert_not_called()

    @patch("src.email_notifier.smtplib.SMTP")
    def test_email_subject_includes_flight_count(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)
        two_flights = [
            self.flight,
            {**self.flight, "id": "offer_002", "destination": "LHR", "price": 800.0},
        ]

        self.notifier.send_notification(RECIPIENT, two_flights)

        sent_raw = mock_server.sendmail.call_args[0][2]
        assert "2" in sent_raw

    @patch("src.email_notifier.smtplib.SMTP")
    def test_email_body_contains_destination(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)

        self.notifier.send_notification(RECIPIENT, [self.flight])

        sent_raw = mock_server.sendmail.call_args[0][2]
        assert "MAD" in sent_raw

    @patch("src.email_notifier.smtplib.SMTP")
    def test_email_body_contains_price(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)

        self.notifier.send_notification(RECIPIENT, [self.flight])

        sent_raw = mock_server.sendmail.call_args[0][2]
        assert "750" in sent_raw

    @patch("src.email_notifier.smtplib.SMTP")
    def test_email_body_contains_airline(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)

        self.notifier.send_notification(RECIPIENT, [self.flight])

        sent_raw = mock_server.sendmail.call_args[0][2]
        assert "IB" in sent_raw

    @patch("src.email_notifier.smtplib.SMTP")
    def test_email_body_sorts_flights_by_price_ascending(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)
        flights = [
            {**self.flight, "destination": "LHR", "price": 860.0},
            {**self.flight, "destination": "MAD", "price": 500.0},
        ]

        self.notifier.send_notification(RECIPIENT, flights)

        sent_raw = mock_server.sendmail.call_args[0][2]
        mad_pos = sent_raw.index("MAD")
        lhr_pos = sent_raw.index("LHR")
        assert mad_pos < lhr_pos

    @patch("src.email_notifier.smtplib.SMTP")
    def test_raises_email_notification_error_on_smtp_failure(self, mock_smtp_cls):
        mock_server = self._mock_smtp(mock_smtp_cls)
        mock_server.sendmail.side_effect = smtplib.SMTPException("Send failed")

        with pytest.raises(EmailNotificationError, match="Send failed"):
            self.notifier.send_notification(RECIPIENT, [self.flight])
