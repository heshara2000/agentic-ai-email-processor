"""Build sample .eml files (email + PDF attachment) for offline demos.

    e:/heshara/Test_task/env4/Scripts/python.exe src/make_sample_email.py
"""
from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path

import config

SAMPLES = [
    ("employee_2.pdf", "New hire onboarding — John Smith", "sample_email_1.eml"),
    ("employee_3.pdf", "Please onboard Maria (paperwork attached)", "sample_email_2.eml"),
    ("employee_4.pdf", "Onboarding form — Daniel O'Connor", "sample_email_3.eml"),
]


def build(pdf_name: str, subject: str, out_name: str) -> None:
    pdf_path = config.DATA_DIR / pdf_name
    if not pdf_path.exists():
        print(f"⚠️  Skipping {out_name}: {pdf_path} not found")
        return

    msg = EmailMessage()
    msg["From"] = "hr@partnercompany.com"
    msg["To"] = "onboarding@flatrock.com"
    msg["Subject"] = subject
    msg.set_content(
        "Hi team,\n\nPlease process the attached onboarding form.\n\nBest regards,\nHR"
    )
    msg.add_attachment(
        pdf_path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=pdf_name,
    )

    out_path = config.DATA_DIR / out_name
    out_path.write_bytes(msg.as_bytes())
    print(f"✅ Wrote {out_path}  (attachment: {pdf_name})")


if __name__ == "__main__":
    for pdf_name, subject, out_name in SAMPLES:
        build(pdf_name, subject, out_name)
