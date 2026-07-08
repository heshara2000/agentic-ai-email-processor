"""Test the RAG validation on the 3 scenarios (clean / messy / mismatch)."""
from __future__ import annotations

import json

from rag import validate_onboarding

CASES = {
    "employee_1 (clean)": {
        "employee_name": "John Smith",
        "email": "john.smith@flatrock.com",
        "department": "Engineering",
        "manager": "Sarah Brown",
        "office": "Colombo",
        "start_date": "2026-08-01",
    },
    "employee_2 (messy - missing manager + bad email)": {
        "employee_name": "Maria Gonzalez-Reyes",
        "email": "maria.reyes(at)flatrock.com",
        "department": "Marketing",
        "manager": "",
        "office": "Kandy",
        "start_date": "next Monday",
    },
    "employee_3 (manager/department mismatch)": {
        "employee_name": "Daniel O'Connor",
        "email": "daniel.oconnor@flatrock.com",
        "department": "Sales",
        "manager": "Sarah Brown",
        "office": "Colombo",
        "start_date": "2026-09-15",
    },
}

for title, record in CASES.items():
    print("=" * 60)
    print(title)
    print("=" * 60)
    result = validate_onboarding(record)
    decision = "🚩 HUMAN REVIEW" if result["needs_human_review"] else "✅ AUTO-APPROVE"
    print("Decision:", decision)
    if result["flags"]:
        print("Flags:")
        for f in result["flags"]:
            print("   -", f)
    print()
