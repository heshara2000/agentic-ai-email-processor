"""Generate a scanned-looking onboarding form image for the demo.

    e:/heshara/Test_task/env4/Scripts/python.exe src/make_sample_image.py

Produces data/employee_scanned.png — read later by the vision model.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

import config

LINES = [
    "EMPLOYEE ONBOARDING FORM",
    "Flat Rock Technology - People Operations",
    "",
    "Full Name:          Priya Fernando",
    "Email Address:      priya.fernando@flatrock.com",
    "Phone:              +94 76 555 1212",
    "Department:         Human Resources",
    "Reporting Manager:  Aisha Khan",
    "Job Title:          HR Coordinator",
    "Employment Type:    Full-Time",
    "Office Location:    Colombo",
    "Start Date:         05 September 2026",
    "",
    "Signed: P. Fernando        Date: 09 July 2026",
]


def _load_font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build() -> None:
    width, height = 900, 620
    # slightly off-white to mimic a scan
    img = Image.new("RGB", (width, height), (247, 246, 242))
    draw = ImageDraw.Draw(img)

    title_font = _load_font(26)
    body_font = _load_font(20)

    y = 40
    for i, line in enumerate(LINES):
        font = title_font if i == 0 else body_font
        draw.text((50, y), line, fill=(30, 30, 30), font=font)
        y += 38 if i == 0 else 34

    # a faint border to look like a page
    draw.rectangle([20, 20, width - 20, height - 20], outline=(180, 180, 180), width=2)

    out_path = config.DATA_DIR / "employee_scanned.png"
    img.save(out_path)
    print(f"✅ Wrote {out_path}")


if __name__ == "__main__":
    build()
