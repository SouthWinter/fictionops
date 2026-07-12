#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(source_path: Path, decision_path: Path) -> dict[str, object]:
    source_bytes = source_path.read_bytes()
    source = source_bytes.decode("utf-8-sig")
    decision = json.loads(decision_path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    if "evidence" in decision:
        errors.append("legacy evidence field is forbidden; use typed evidence fields only")

    evidence = decision.get("manuscript_evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("manuscript_evidence must be a non-empty array of strings")
        evidence = []

    authority_evidence = decision.get("authority_evidence")
    if not isinstance(authority_evidence, list) or not authority_evidence:
        errors.append("authority_evidence must be a non-empty array")
    else:
        for index, item in enumerate(authority_evidence, start=1):
            if not isinstance(item, dict) or not str(item.get("source", "")).strip() or not str(item.get("support", "")).strip():
                errors.append(f"authority_evidence item {index} requires non-empty source and support")

    if decision.get("manuscript_edited") is not False:
        errors.append("manuscript_edited must be explicitly false for a frozen teacher review")
    if decision.get("teacher_ground_truth") is not False:
        errors.append("teacher_ground_truth must be explicitly false")

    source_normalized = normalized(source)
    matches: list[dict[str, object]] = []
    for index, quote in enumerate(evidence, start=1):
        is_string = isinstance(quote, str)
        is_nonempty = is_string and bool(quote.strip())
        matched = bool(is_nonempty and normalized(quote) in source_normalized)
        matches.append(
            {
                "index": index,
                "matched": matched,
                "quote_sha256": sha256(quote.encode("utf-8")) if is_string else None,
                "reason": None if matched else "not an exact source substring after whitespace normalization",
            }
        )

    return {
        "schema": "fictionops.teacher_evidence_verification.v1",
        "status": "pass" if not errors and all(item["matched"] for item in matches) else "fail",
        "source_sha256": sha256(source_bytes),
        "field": "manuscript_evidence",
        "evidence_count": len(matches),
        "authority_evidence_count": len(authority_evidence) if isinstance(authority_evidence, list) else 0,
        "errors": errors,
        "matches": matches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that teacher manuscript evidence exactly occurs in a frozen UTF-8 source."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("decision", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    result = verify(args.source, args.decision)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
