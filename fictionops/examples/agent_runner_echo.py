from __future__ import annotations

import json
import re
import sys


REQUEST_BLOCK = re.compile(r"## Request\s+```json\s*(.*?)\s*```", re.DOTALL)


def extract_request(payload: str) -> dict[str, object]:
    match = REQUEST_BLOCK.search(payload)
    if not match:
        raise ValueError("missing FictionOps request JSON block")
    data = json.loads(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("FictionOps request must be a JSON object")
    return data


def text_value(request: dict[str, object], key: str, default: str = "-") -> str:
    value = request.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def read_stdin_utf8() -> str:
    return sys.stdin.buffer.read().decode("utf-8")


def main() -> int:
    payload = read_stdin_utf8()
    request = extract_request(payload)
    role = text_value(request, "role")
    task = text_value(request, "task")
    book = text_value(request, "book", "book_01")
    chapter = text_value(request, "chapter")
    provider = text_value(request, "provider")
    model = text_value(request, "model")

    print("# Echo Agent Staging Output")
    print()
    print("> This demo runner does not call a model. Replace this section with your model or agent call.")
    print()
    print("## Request Summary")
    print()
    print(f"- Role: `{role}`")
    print(f"- Task: `{task}`")
    print(f"- Book: `{book}`")
    print(f"- Chapter: `{chapter}`")
    print(f"- Provider: `{provider}`")
    print(f"- Model: `{model}`")
    print(f"- Input chars: {len(payload)}")
    print()
    print("## Staged Result")
    print()
    print("The external runner received a complete FictionOps task bundle and returned this staged output.")
    print("Review it with `fictionops agent-inbox` before applying anything to manuscript or canon files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
