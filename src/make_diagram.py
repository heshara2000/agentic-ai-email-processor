"""Render docs/architecture.mmd to a PNG using the mermaid.ink service.

    e:/heshara/Test_task/env4/Scripts/python.exe src/make_diagram.py

Requires an internet connection (uses the free mermaid.ink renderer).
Output: docs/architecture.png
"""
from __future__ import annotations

import base64
import json
import urllib.request
import zlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MMD_FILE = PROJECT_ROOT / "docs" / "architecture.mmd"
PNG_FILE = PROJECT_ROOT / "docs" / "architecture.png"


def _encode(graph: str) -> str:
    """Encode the graph in the pako format mermaid.ink expects."""
    state = {"code": graph, "mermaid": {"theme": "default"}}
    raw = json.dumps(state).encode("utf-8")
    compressed = zlib.compress(raw, 9)
    return "pako:" + base64.urlsafe_b64encode(compressed).decode("ascii")


def main() -> int:
    if not MMD_FILE.exists():
        print(f"❌ Diagram source not found: {MMD_FILE}")
        return 1

    graph = MMD_FILE.read_text(encoding="utf-8")
    url = f"https://mermaid.ink/img/{_encode(graph)}?type=png"

    print("Rendering diagram via mermaid.ink ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Could not render online: {type(exc).__name__}: {exc}")
        print("   Alternative: open https://mermaid.live , paste docs/architecture.mmd,")
        print("   then Export -> PNG and save it as docs/architecture.png")
        return 1

    PNG_FILE.write_bytes(data)
    print(f"✅ Saved diagram to {PNG_FILE}  ({len(data):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
