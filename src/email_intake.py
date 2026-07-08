"""Email intake: pick up an email with a file attachment and run the pipeline.

Two modes:

  # Offline: read a saved .eml file (great for demos)
  e:/heshara/Test_task/env4/Scripts/python.exe src/email_intake.py eml data/sample_email.eml

  # Live: poll an IMAP inbox (Gmail etc.) for UNREAD messages with attachments
  e:/heshara/Test_task/env4/Scripts/python.exe src/email_intake.py imap
"""
from __future__ import annotations

import email
import imaplib
import sys
from email import policy
from pathlib import Path

import config
from main import process_document

INBOX_DIR = config.DATA_DIR / "inbox"
INBOX_DIR.mkdir(parents=True, exist_ok=True)

# Attachment types the pipeline can currently handle.
SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".csv"}


def _save_attachments(msg, out_dir: Path) -> list[str]:
    """Save every supported attachment from an email message to out_dir."""
    saved: list[str] = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        if not filename:
            continue
        if Path(filename).suffix.lower() not in SUPPORTED_SUFFIXES:
            print(f"   skipping unsupported attachment: {filename}")
            continue
        data = part.get_payload(decode=True)
        if not data:
            continue
        dest = out_dir / filename
        dest.write_bytes(data)
        saved.append(str(dest))
        print(f"   saved attachment: {dest}")
    return saved


def from_eml(eml_path: str) -> list[tuple[str, str]]:
    """Extract attachments from a local .eml file. Returns [(path, sender)]."""
    print(f"Reading email file: {eml_path}")
    with open(eml_path, "rb") as fh:
        msg = email.message_from_binary_file(fh, policy=policy.default)
    sender = str(msg["from"] or "unknown")
    print(f"   From   : {sender}")
    print(f"   Subject: {msg['subject']}")
    return [(path, sender) for path in _save_attachments(msg, INBOX_DIR)]


def from_imap() -> list[tuple[str, str]]:
    """Fetch attachments from UNREAD messages in a live IMAP inbox. Returns [(path, sender)]."""
    if (
        not config.IMAP_USER
        or not config.IMAP_PASSWORD
        or config.IMAP_PASSWORD == "your-app-password"
    ):
        print("⚠️  IMAP not configured. Set IMAP_USER and IMAP_PASSWORD in .env first.")
        print("   (Gmail: create an App Password at https://myaccount.google.com/apppasswords)")
        return []

    print(f"Connecting to {config.IMAP_HOST} as {config.IMAP_USER} ...")
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USER, config.IMAP_PASSWORD)
    imap.select(config.IMAP_FOLDER)

    _, data = imap.search(None, "UNSEEN")
    message_ids = data[0].split()
    print(f"   {len(message_ids)} unread message(s) found")

    saved: list[tuple[str, str]] = []
    for num in message_ids:
        _, msg_data = imap.fetch(num, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw, policy=policy.default)
        sender = str(msg["from"] or "unknown")
        print(f"   Email from {sender} | {msg['subject']}")
        saved.extend((path, sender) for path in _save_attachments(msg, INBOX_DIR))

    imap.logout()
    return saved


def run(mode: str, arg: str | None) -> int:
    if mode == "eml":
        if not arg:
            print("Usage: python src/email_intake.py eml <path-to-.eml>")
            return 1
        attachments = from_eml(arg)
    elif mode == "imap":
        attachments = from_imap()
    else:
        print("Unknown mode. Use:  eml <file>   or   imap")
        return 1

    if not attachments:
        print("No supported attachments found.")
        return 0

    print(f"\nPicked up {len(attachments)} attachment(s). Running the pipeline...\n")
    for path, sender in attachments:
        process_document(path, sender=sender)
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "imap"
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(run(mode, arg))
