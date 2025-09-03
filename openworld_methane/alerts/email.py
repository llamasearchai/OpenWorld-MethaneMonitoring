from __future__ import annotations

import smtplib
from collections.abc import Iterable
from email.message import EmailMessage

from ..models import Anomaly, EmissionRecord
from . import Alert


class EmailAlerter(Alert):
    def __init__(
        self,
        *,
        smtp_host: str,
        smtp_port: int = 25,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
        sender: str,
        recipients: Iterable[str],
        dry_run: bool = False,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender = sender
        self.recipients = list(recipients)
        self.dry_run = dry_run

    def _build_message(self, subject: str, body: str) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject
        msg.set_content(body)
        return msg

    def send_text(self, text: str) -> None:  # conforms to Alert
        # Default subject for plain text
        msg = self._build_message("OpenWorld Alert", text)
        if self.dry_run:
            print(f"[DRY-RUN EMAIL] to={self.recipients} subject=OpenWorld Alert\n{text}")
            return
        if self.use_tls:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.starttls()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(msg)

    def send_message(self, subject: str, body: str) -> None:
        msg = self._build_message(subject, body)
        if self.dry_run:
            print(f"[DRY-RUN EMAIL] to={self.recipients} subject={subject}\n{body}")
            return
        if self.use_tls:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.starttls()
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(msg)

    def send_anomalies(self, anomalies: Iterable[Anomaly]) -> int:
        anomalies = list(anomalies)
        if not anomalies:
            return 0
        lines = []
        for a in anomalies:
            r: EmissionRecord = a.record
            lines.append(
                f"[{r.timestamp.isoformat()}] site={r.site_id} region={r.region_id} "
                f"rate={r.emission_rate_kg_per_h:.3f} kg/h z={a.score:.2f}"
            )
        subject = f"OpenWorld: {len(anomalies)} methane anomalies detected"
        body = "\n".join(lines)
        self.send_message(subject, body)
        return len(anomalies)
