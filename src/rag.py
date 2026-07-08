"""RAG validation: query the ChromaDB knowledge base to validate an extraction.

The knowledge base (built by build_kb.py) contains:
  - the department -> manager directory
  - the onboarding policy rules

This module cross-references the extracted data against that knowledge and
returns a list of flags plus a human-review decision. This is the step that
turns raw extraction into a validated, routable result.
"""
from __future__ import annotations

from build_kb import get_collection


def retrieve(query: str, n: int = 3, where: dict | None = None) -> list[tuple[str, dict]]:
    """Semantic search the knowledge base. Returns [(document_text, metadata)]."""
    result = get_collection().query(query_texts=[query], n_results=n, where=where)
    docs = result["documents"][0]
    metas = result["metadatas"][0]
    return list(zip(docs, metas))


def _norm(value) -> str:
    return str(value or "").strip().lower()


def _loose_match(a: str, b: str) -> bool:
    """True if either normalized string contains the other (handles messy names)."""
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return False
    return a in b or b in a


def validate_onboarding(data: dict) -> dict:
    """Validate extracted onboarding data against the RAG knowledge base.

    Returns a dict with per-check results, human-readable flags, the supporting
    policy snippets that were retrieved, and a needs_human_review decision.
    """
    flags: list[str] = []
    checks: list[dict] = []

    # 1) Required fields present?
    required = ["employee_name", "email", "department", "manager", "start_date"]
    missing = [f for f in required if not _norm(data.get(f))]
    if missing:
        flags.append("Missing required fields: " + ", ".join(missing))
    checks.append({"name": "required_fields", "passed": not missing, "detail": missing})

    # 2) Is the department real? (RAG lookup in the directory)
    department = data.get("department", "")
    matched_department = None
    expected_manager = None
    known_department = False
    if department:
        hits = retrieve(f"{department} department manager", n=1, where={"type": "department"})
        if hits:
            _, meta = hits[0]
            matched_department = meta.get("department")
            expected_manager = meta.get("manager")
            known_department = _loose_match(matched_department, department)
    if not known_department:
        flags.append(f"Unknown department '{department}' — not in company directory")
    checks.append({
        "name": "known_department",
        "passed": known_department,
        "detail": matched_department,
    })

    # 3) Does the manager actually manage that department? (RAG cross-reference)
    manager = data.get("manager", "")
    if known_department and manager and expected_manager:
        manager_ok = _loose_match(manager, expected_manager)
        if not manager_ok:
            flags.append(
                f"Manager '{manager}' does not manage {matched_department} "
                f"(directory shows {expected_manager})"
            )
        checks.append({
            "name": "manager_matches_department",
            "passed": manager_ok,
            "detail": expected_manager,
        })

    # 3b) Is the manager a real manager at all? (RAG lookup in the manager directory)
    if manager:
        manager_hits = retrieve(f"{manager} manager", n=1, where={"type": "manager"})
        known_manager = bool(manager_hits) and _loose_match(
            manager_hits[0][1].get("manager", ""), manager
        )
        if not known_manager:
            flags.append(f"Unknown manager '{manager}' — not in the manager directory")
        checks.append({"name": "known_manager", "passed": known_manager, "detail": manager})

    # 4) Policy: work email must be @flatrock.com
    email = data.get("email", "")
    if email:
        email_ok = "@flatrock.com" in _norm(email)
        if not email_ok:
            flags.append(f"Email '{email}' is not a valid @flatrock.com address")
        checks.append({"name": "email_domain", "passed": email_ok, "detail": email})

    # 5) Is the office an approved location? (RAG lookup)
    office = data.get("office", "")
    office_ok = False
    if office:
        office_hits = retrieve(f"{office} office location", n=1, where={"type": "office"})
        if office_hits:
            _, meta = office_hits[0]
            office_ok = _loose_match(meta.get("office", ""), office)
        if not office_ok:
            flags.append(f"Office '{office}' is not an approved location")
        checks.append({"name": "office_valid", "passed": office_ok, "detail": office})

    # Retrieve the policy rules most relevant to this record (for transparency).
    policy_query = (
        f"{data.get('department', '')} {data.get('employee_name', '')} "
        f"start date {data.get('start_date', '')} email {email}"
    )
    relevant_policies = [doc for doc, _ in retrieve(policy_query, n=3, where={"type": "policy"})]

    # Field-level validity summary (handy for the saved JSON record).
    manager_ok = any(
        c["name"] == "manager_matches_department" and c["passed"] for c in checks
    )
    field_validation = {
        "department_valid": known_department,
        "manager_valid": manager_ok,
        "office_valid": office_ok,
    }

    # Confidence = share of validation checks that passed.
    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    confidence = round(passed / total, 2) if total else 0.0

    needs_human_review = len(flags) > 0
    return {
        "checks": checks,
        "field_validation": field_validation,
        "confidence": confidence,
        "flags": flags,
        "relevant_policies": relevant_policies,
        "matched_department": matched_department,
        "expected_manager": expected_manager,
        "needs_human_review": needs_human_review,
    }
