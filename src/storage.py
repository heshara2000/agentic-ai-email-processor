"""Routing & storage: act on the validated result.

- Clean, high-confidence records  -> outputs/approved.csv
- Anything flagged by RAG/policy   -> outputs/human_review.csv (with reasons)

This is the "routing & action" step: the agent does something useful with what
it found, and anything it isn't sure about is sent for human review.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone

import config

APPROVED_CSV = config.OUTPUT_DIR / "approved.csv"
REVIEW_CSV = config.OUTPUT_DIR / "human_review.csv"

FIELDNAMES = [
    "timestamp",
    "source_file",
    "employee_name",
    "email",
    "department",
    "manager",
    "office",
    "start_date",
    "decision",
    "flags",
]


def _append_row(path, row: dict) -> None:
    write_header = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def route_and_store(source_file: str, data: dict, validation: dict) -> dict:
    """Route a single processed document to the right CSV and return a summary."""
    needs_review = validation.get("needs_human_review", True)
    decision = "HUMAN_REVIEW" if needs_review else "APPROVED"

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_file": source_file,
        "employee_name": data.get("employee_name", ""),
        "email": data.get("email", ""),
        "department": data.get("department", ""),
        "manager": data.get("manager", ""),
        "office": data.get("office", ""),
        "start_date": data.get("start_date", ""),
        "decision": decision,
        "flags": " | ".join(validation.get("flags", [])),
    }

    target = REVIEW_CSV if needs_review else APPROVED_CSV
    _append_row(target, row)

    return {"decision": decision, "stored_in": str(target), "row": row}
