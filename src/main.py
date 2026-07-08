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
from nodes import extract_records
from rag import validate_onboarding
from storage import route_and_store, save_result_json


def process_document(file_path: str, sender: str | None = None) -> list[dict]:
    """Run one file through the full pipeline. A CSV may yield several records.

    Never raises — a bad/corrupt file is routed to human review instead.
    """
    print("=" * 64)
    print(f"PROCESSING: {file_path}")
    print("=" * 64)

    try:
        records = extract_records(file_path)
    except Exception as exc:  # noqa: BLE001 - a bad/corrupt file must not crash the batch
        print(f"❌ Could not read/extract this file: {type(exc).__name__}: {exc}")
        validation = {
            "needs_human_review": True,
            "flags": [f"Extraction failed: {type(exc).__name__}"],
            "field_validation": {},
            "confidence": 0.0,
        }
        result = route_and_store(file_path, {}, validation)
        save_result_json(file_path, {}, validation, sender=sender)
        print(f"Decision: 🚩 HUMAN REVIEW  ->  {result['stored_in']}\n")
        return [result]

    results: list[dict] = []
    for i, data in enumerate(records, start=1):
        if len(records) > 1:
            print(f"\n--- Record {i} of {len(records)} ---")

        validation = validate_onboarding(data)
        result = route_and_store(file_path, data, validation)
        json_path = save_result_json(file_path, data, validation, sender=sender, index=i)
        results.append(result)

        print("Extracted:")
        for key, value in data.items():
            print(f"   {key:15}: {value}")

        if validation.get("needs_human_review"):
            print("\nDecision: 🚩 HUMAN REVIEW")
            for flag in validation.get("flags", []):
                print(f"   - {flag}")
        else:
            print("\nDecision: ✅ AUTO-APPROVE")
        print(f"Confidence: {validation.get('confidence')}")
        print(f"Stored in : {result['stored_in']}")
        print(f"JSON      : {json_path}")

    print()
    return results


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        files = argv[1:]
    else:
        patterns = ["employee_*.pdf", "*.png", "*.jpg", "*.jpeg", "onboarding*.csv"]
        files = []
        for pattern in patterns:
            files.extend(glob.glob(str(config.DATA_DIR / pattern)))
        files = sorted(set(files))

    if not files:
        print("No files to process. Put files in the data/ folder or pass a path.")
        return 1

    approved = review = 0
    for file_path in files:
        try:
            results = process_document(file_path)
        except Exception:  # noqa: BLE001 - keep the batch going
            traceback.print_exc()
            review += 1
            continue
        for result in results:
            if result["decision"] == "APPROVED":
                approved += 1
            else:
                review += 1

    print("=" * 64)
    print(f"DONE. Approved: {approved}   Human review: {review}")
    print(f"  Approved CSV     : {config.OUTPUT_DIR / 'approved.csv'}")
    print(f"  Human-review CSV : {config.OUTPUT_DIR / 'human_review.csv'}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
