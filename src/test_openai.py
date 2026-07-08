"""Quick connectivity test for the OpenAI API key.

Run:  e:/heshara/Test_task/env4/Scripts/python.exe src/test_openai.py
"""
from __future__ import annotations

import sys

from openai import OpenAI, AuthenticationError

import config


def main() -> int:
    key = config.OPENAI_API_KEY.strip()

    if not key or key.startswith("sk-your-key"):
        print(" No API key found.")
        print("   -> Create a file named '.env' in the project root")
        print("   -> Add this line:  OPENAI_API_KEY=sk-...your real key...")
        return 1

    masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "(too short)"
    print(f"Using model : {config.OPENAI_MODEL}")
    print(f"Using key   : {masked}  (length {len(key)})")

    client = OpenAI(api_key=key)
    try:
        resp = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=5,
        )
    except AuthenticationError:
        print("\n 401 Unauthorized — the API key is not valid.")
        print("   Fix checklist:")
        print("   1. Copy the FULL key from https://platform.openai.com/api-keys")
        print("      (starts with sk-... , no spaces, not truncated)")
        print("   2. Paste it into .env as:  OPENAI_API_KEY=sk-...")
        print("   3. Make sure the project/org has billing or free credits.")
        print("   4. If it was ever shown publicly, OpenAI auto-revokes it — make a new one.")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"\n Unexpected error: {type(exc).__name__}: {exc}")
        return 1

    print("\n Success! Model replied:", resp.choices[0].message.content)
    return 0


if __name__ == "__main__":
    sys.exit(main())