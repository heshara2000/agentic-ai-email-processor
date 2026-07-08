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

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Loaded {len(documents)} documents into '{COLLECTION_NAME}'.")
    print(f"   Departments: {sum(1 for m in metadatas if m['type'] == 'department')}")
    print(f"   Policy rules: {sum(1 for m in metadatas if m['type'] == 'policy')}")


if __name__ == "__main__":
    build()
