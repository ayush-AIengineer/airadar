"""Email channel senders (Architecture §4.5).

Two interchangeable backends behind one interface, mirroring the enrichment extractor
split (offline stub ↔ real API):

- :class:`ConsoleEmailSender` — writes rendered digests to the local outbox dir. Zero
  keys, zero network; lets the whole Delivery stage run offline end-to-end.
- :class:`ResendEmailSender` — sends for real via Resend. Lazy-imports ``resend`` so the
  base install never needs it.

:func:`get_email_sender` picks the backend from settings (Resend key present → real).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from loguru import logger

from airadar.config import Settings
from airadar.delivery.renderers import RenderedEmail


class EmailSender(Protocol):
    async def send(self, *, to: str, sender: str, email: RenderedEmail) -> str:
        """Send the email; return a delivery status string ('sent' | 'failed' | ...)."""
        ...


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


class ConsoleEmailSender:
    """Offline sender: writes the rendered email to ``outbox_dir`` and logs a summary."""

    def __init__(self, outbox_dir: str) -> None:
        self._dir = Path(outbox_dir)

    async def send(self, *, to: str, sender: str, email: RenderedEmail) -> str:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{_safe_name(to)}.html"
        path.write_text(email.html, encoding="utf-8")
        logger.info("Console email → {} ({!r}) written to {}", to, email.subject, path)
        return "sent"


class ResendEmailSender:
    """Real transactional email via Resend."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def send(self, *, to: str, sender: str, email: RenderedEmail) -> str:
        import resend

        resend.api_key = self._api_key
        try:
            resend.Emails.send(
                {
                    "from": sender,
                    "to": [to],
                    "subject": email.subject,
                    "html": email.html,
                    "text": email.text,
                }
            )
        except Exception as exc:  # noqa: BLE001 — record failure, don't crash the batch
            logger.error("Resend send to {} failed: {}", to, exc)
            return "failed"
        return "sent"


def get_email_sender(settings: Settings) -> EmailSender:
    if settings.resend_api_key:
        return ResendEmailSender(settings.resend_api_key)
    return ConsoleEmailSender(settings.delivery_outbox_dir)
