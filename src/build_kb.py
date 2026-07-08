"""Build the RAG knowledge base: load knowledge documents into ChromaDB.

Run once (or whenever the knowledge files change):
    e:/heshara/Test_task/env4/Scripts/python.exe src/build_kb.py
"""
from __future__ import annotations

import re

import chromadb

import config

COLLECTION_NAME = "onboarding_kb"


def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def get_collection():
    """Return the knowledge-base collection (creates it if missing)."""
    return _client().get_or_create_collection(name=COLLECTION_NAME)


def build() -> None:
    client = _client()

    # Start clean so re-running doesn't create duplicates.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:  # noqa: BLE001 - collection may not exist yet
        pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    # 1) Department directory -> one doc per department, with structured metadata.
    dept_file = config.KNOWLEDGE_DIR / "departments.md"
    dept_text = dept_file.read_text(encoding="utf-8")
    pattern = re.compile(r"(.+?) department is managed by (.+?)\.", re.IGNORECASE)
    for i, match in enumerate(pattern.finditer(dept_text)):
        department = match.group(1).strip()
        manager = match.group(2).strip()
        documents.append(f"{department} department is managed by {manager}.")
        metadatas.append({"type": "department", "department": department, "manager": manager})
        ids.append(f"dept-{i}")

    # 2) Onboarding policy -> one doc per rule line.
    policy_file = config.KNOWLEDGE_DIR / "onboarding_policy.md"
    for i, line in enumerate(policy_file.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        documents.append(line)
        metadatas.append({"type": "policy"})
        ids.append(f"policy-{i}")

    # 3) Approved office locations -> one doc per office.
    offices_file = config.KNOWLEDGE_DIR / "offices.md"
    office_pattern = re.compile(r"^(.+?) is an approved", re.IGNORECASE)
    for i, line in enumerate(offices_file.read_text(encoding="utf-8").splitlines()):
        match = office_pattern.match(line.strip())
        if not match:
            continue
        office = match.group(1).strip()
        documents.append(line.strip())
        metadatas.append({"type": "office", "office": office})
        ids.append(f"office-{i}")

    # 4) Manager directory -> one doc per manager, with structured metadata.
    managers_file = config.KNOWLEDGE_DIR / "managers.md"
    manager_pattern = re.compile(r"^(.+?) is a manager in the (.+?) department", re.IGNORECASE)
    for i, line in enumerate(managers_file.read_text(encoding="utf-8").splitlines()):
        match = manager_pattern.match(line.strip())
        if not match:
            continue
        manager = match.group(1).strip()
        department = match.group(2).strip()
        documents.append(line.strip())
        metadatas.append({"type": "manager", "manager": manager, "department": department})
        ids.append(f"manager-{i}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Loaded {len(documents)} documents into '{COLLECTION_NAME}'.")
    print(f"   Departments: {sum(1 for m in metadatas if m['type'] == 'department')}")
    print(f"   Policy rules: {sum(1 for m in metadatas if m['type'] == 'policy')}")
    print(f"   Offices: {sum(1 for m in metadatas if m['type'] == 'office')}")
    print(f"   Managers: {sum(1 for m in metadatas if m['type'] == 'manager')}")


if __name__ == "__main__":
    build()
