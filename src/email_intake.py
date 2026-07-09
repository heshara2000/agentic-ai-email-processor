"""Email intake: pick up unread emails with attachments and run the pipeline.

    python src/email_intake.py

Connects to a live IMAP inbox (e.g. Gmail), finds the most recent UNREAD
messages with supported attachments, saves them, and runs each through the
full pipeline (extract -> RAG validate -> route -> store).
"""
from __future__ import annotations

import email
import imaplib
import os
import sys
from email import policy
from pathlib import Path

import config
from logger import get_logger
from main import process_document

log = get_logger()

INBOX_DIR = config.DATA_DIR / "inbox"
INBOX_DIR.mkdir(parents=True, exist_ok=True)

# Attachment types the pipeline can currently handle.
SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".csv"}

# Safety limits for a real inbox: never churn through hundreds of old emails.
MAX_EMAILS = int(os.getenv("IMAP_MAX_EMAILS", "5"))
# Optional: only pick up emails whose subject contains this text (set in .env).
SUBJECT_FILTER = os.getenv("IMAP_SUBJECT_FILTER", "").strip()


def _save_attachments(msg, out_dir: Path) -> list[str]:
    """Save every supported attachment from an email message to out_dir."""
    saved: list[str] = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        if not filename:
            continue
        if Path(filename).suffix.lower() not in SUPPORTED_SUFFIXES:
            log.warning("   skipping unsupported attachment: %s", filename)
            continue
        data = part.get_payload(decode=True)
        if not data:
            continue
        dest = out_dir / filename
        dest.write_bytes(data)
        saved.append(str(dest))
        log.info("   saved attachment: %s", dest)
    return saved


def from_imap() -> list[tuple[str, str]]:
    """Fetch attachments from UNREAD messages in a live IMAP inbox. Returns [(path, sender)]."""
    if (
        not config.IMAP_USER
        or not config.IMAP_PASSWORD
        or config.IMAP_PASSWORD == "your-app-password"
    ):
        log.warning("IMAP not configured. Set IMAP_USER and IMAP_PASSWORD in .env first.")
        log.warning("   (Gmail: create an App Password at https://myaccount.google.com/apppasswords)")
        return []

    log.info("Connecting to %s as %s ...", config.IMAP_HOST, config.IMAP_USER)
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USER, config.IMAP_PASSWORD)
    imap.select(config.IMAP_FOLDER)

    criteria = ["UNSEEN"]
    if SUBJECT_FILTER:
        criteria += ["SUBJECT", SUBJECT_FILTER]
    _, data = imap.search(None, *criteria)
    message_ids = data[0].split()

    # Only handle the most recent MAX_EMAILS messages (newest first).
    recent_ids = message_ids[-MAX_EMAILS:]
    log.info(
        "   %d unread message(s) found; processing the %d most recent",
        len(message_ids),
        len(recent_ids),
    )

    saved: list[tuple[str, str]] = []
    for num in reversed(recent_ids):
        _, msg_data = imap.fetch(num, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw, policy=policy.default)
        sender = str(msg["from"] or "unknown")
        log.info("   Email from %s | %s", sender, msg["subject"])
        saved.extend((path, sender) for path in _save_attachments(msg, INBOX_DIR))

    imap.logout()
    return saved


def run() -> int:
    attachments = from_imap()
    if not attachments:
        log.warning("No supported attachments found.")
        return 0

    log.info("Picked up %d attachment(s). Running the pipeline...", len(attachments))
    for path, sender in attachments:
        process_document(path, sender=sender)
    return 0


if __name__ == "__main__":
    sys.exit(run())
