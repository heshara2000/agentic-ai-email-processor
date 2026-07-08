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

import config
from logger import get_logger
from nodes import extract_records
from rag import validate_onboarding
from storage import route_and_store, save_result_json

log = get_logger()


def process_document(file_path: str, sender: str | None = None) -> list[dict]:
    """Run one file through the full pipeline. A CSV may yield several records.

    Never raises — a bad/corrupt file is routed to human review instead.
    """
    log.info("=" * 64)
    log.info("PROCESSING: %s", file_path)
    log.info("=" * 64)

    try:
        records = extract_records(file_path)
    except Exception as exc:  # noqa: BLE001 - a bad/corrupt file must not crash the batch
        log.error("Could not read/extract this file: %s: %s", type(exc).__name__, exc)
        validation = {
            "needs_human_review": True,
            "flags": [f"Extraction failed: {type(exc).__name__}"],
            "field_validation": {},
            "confidence": 0.0,
        }
        result = route_and_store(file_path, {}, validation)
        save_result_json(file_path, {}, validation, sender=sender)
        log.warning("Decision: HUMAN REVIEW -> %s", result["stored_in"])
        return [result]

    results: list[dict] = []
    for i, data in enumerate(records, start=1):
        if len(records) > 1:
            log.info("--- Record %d of %d ---", i, len(records))

        validation = validate_onboarding(data)
        result = route_and_store(file_path, data, validation)
        json_path = save_result_json(file_path, data, validation, sender=sender, index=i)
        results.append(result)

        log.info("Extracted:")
        for key, value in data.items():
            log.info("   %-15s: %s", key, value)

        if validation.get("needs_human_review"):
            log.warning("Decision: HUMAN REVIEW")
            for flag in validation.get("flags", []):
                log.warning("   - %s", flag)
        else:
            log.info("Decision: AUTO-APPROVE")
        log.info("Confidence: %s", validation.get("confidence"))
        log.info("Stored in : %s", result["stored_in"])
        log.info("JSON      : %s", json_path)

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
        log.warning("No files to process. Put files in the data/ folder or pass a path.")
        return 1

    approved = review = 0
    for file_path in files:
        try:
            results = process_document(file_path)
        except Exception:  # noqa: BLE001 - keep the batch going
            log.exception("Unexpected error while processing %s", file_path)
            review += 1
            continue
        for result in results:
            if result["decision"] == "APPROVED":
                approved += 1
            else:
                review += 1

    log.info("=" * 64)
    log.info("DONE. Approved: %d   Human review: %d", approved, review)
    log.info("  Approved CSV     : %s", config.OUTPUT_DIR / "approved.csv")
    log.info("  Human-review CSV : %s", config.OUTPUT_DIR / "human_review.csv")
    log.info("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
