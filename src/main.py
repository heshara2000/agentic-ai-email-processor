"""End-to-end pipeline: extract -> RAG validate -> route -> store.

Usage:
    # process every PDF in the data/ folder
    e:/heshara/Test_task/env4/Scripts/python.exe src/main.py

    # process a single file
    e:/heshara/Test_task/env4/Scripts/python.exe src/main.py data/employee_2.pdf
"""
from __future__ import annotations

import glob
import sys
import traceback

import config
from nodes import extract_employee_json
from rag import validate_onboarding
from storage import route_and_store


def process_document(file_path: str) -> dict:
    """Run one document through the full pipeline. Never raises — errors are routed to review."""
    print("=" * 64)
    print(f"PROCESSING: {file_path}")
    print("=" * 64)

    try:
        data = extract_employee_json(file_path)
    except Exception as exc:  # noqa: BLE001 - a bad/corrupt file must not crash the batch
        print(f"❌ Could not read/extract this file: {type(exc).__name__}: {exc}")
        validation = {
            "needs_human_review": True,
            "flags": [f"Extraction failed: {type(exc).__name__}"],
        }
        result = route_and_store(file_path, {}, validation)
        print(f"Decision: 🚩 HUMAN REVIEW  ->  {result['stored_in']}\n")
        return result

    validation = validate_onboarding(data)
    result = route_and_store(file_path, data, validation)

    print("Extracted:")
    for key, value in data.items():
        print(f"   {key:15}: {value}")

    if validation.get("needs_human_review"):
        print("\nDecision: 🚩 HUMAN REVIEW")
        for flag in validation.get("flags", []):
            print(f"   - {flag}")
    else:
        print("\nDecision: ✅ AUTO-APPROVE")

    print(f"Stored in: {result['stored_in']}\n")
    return result


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        files = argv[1:]
    else:
        files = sorted(glob.glob(str(config.DATA_DIR / "employee_*.pdf")))

    if not files:
        print("No files to process. Put PDFs in the data/ folder or pass a path.")
        return 1

    approved = review = 0
    for file_path in files:
        try:
            result = process_document(file_path)
            if result["decision"] == "APPROVED":
                approved += 1
            else:
                review += 1
        except Exception:  # noqa: BLE001 - keep the batch going
            traceback.print_exc()
            review += 1

    print("=" * 64)
    print(f"DONE. Approved: {approved}   Human review: {review}")
    print(f"  Approved CSV     : {config.OUTPUT_DIR / 'approved.csv'}")
    print(f"  Human-review CSV : {config.OUTPUT_DIR / 'human_review.csv'}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
