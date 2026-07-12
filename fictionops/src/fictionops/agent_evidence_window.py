from __future__ import annotations

import hashlib
import json
import re
from typing import Any


REVERIFICATION_EVIDENCE_WINDOW_SCHEMA = "fictionops.reverification_evidence_window.v1"


def _finding(sample: dict[str, Any]) -> dict[str, Any]:
    value = sample.get("reviewer_finding")
    return value if isinstance(value, dict) else {}


def _fragments(sample: dict[str, Any]) -> list[str]:
    finding = _finding(sample)
    verifier = sample.get("verifier_assessment") if isinstance(sample.get("verifier_assessment"), dict) else {}
    values: list[Any] = []
    evidence = finding.get("evidence")
    values.extend(evidence if isinstance(evidence, list) else [evidence])
    values.extend(verifier.get("evidence") or [])
    fragments: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if len(text) >= 4:
            fragments.append(text)
        for groups in re.findall(r"'([^']+)'|\"([^\"]+)\"|“([^”]+)”|‘([^’]+)’", text):
            fragments.extend(part.strip() for part in groups if len(part.strip()) >= 4)
    return list(dict.fromkeys(fragments))


def _paragraph_window(text: str, fragments: list[str], *, radius: int, max_chars: int) -> str:
    if not text or max_chars <= 0:
        return ""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    matches = {
        index
        for index, paragraph in enumerate(paragraphs)
        if any(fragment in paragraph or fragment[:24] in paragraph for fragment in fragments)
    }
    if not matches:
        return text[:max_chars].rstrip()
    selected: set[int] = set()
    for index in matches:
        selected.update(range(max(0, index - radius), min(len(paragraphs), index + radius + 1)))
    output: list[str] = []
    used = 0
    for index in sorted(selected):
        paragraph = paragraphs[index]
        extra = len(paragraph) + (2 if output else 0)
        if used + extra > max_chars:
            remaining = max_chars - used - (2 if output else 0)
            if remaining > 0:
                output.append(paragraph[:remaining].rstrip())
            break
        output.append(paragraph)
        used += extra
    return "\n\n".join(output).rstrip()


def _is_bounded_claim(sample: dict[str, Any]) -> bool:
    finding = _finding(sample)
    preserve = finding.get("preserve_constraints")
    preserve_text = " ".join(str(item) for item in preserve) if isinstance(preserve, list) else str(preserve or "")
    text = "\n".join(
        [
            str(finding.get("problem") or ""),
            str(finding.get("suggested_action") or ""),
            preserve_text,
        ]
    ).casefold()
    markers = (
        "only these",
        "only this",
        "exact quote",
        "bounded",
        "preserve all other",
        "只改",
        "仅改",
        "这两处",
        "这一处",
        "其余",
        "不在本轮",
    )
    guards = sample.get("active_author_guards")
    has_author_boundary = bool(guards) or bool(preserve_text.strip())
    return bool(_fragments(sample)) and has_author_boundary and any(marker in text for marker in markers)


def _raw_source_chars(request: dict[str, Any], sample: dict[str, Any]) -> int:
    guards = json.dumps(sample.get("active_author_guards") or {}, ensure_ascii=False, indent=2)
    evidence_chars = sum(
        len(str(item.get("content") or ""))
        for item in request.get("evidence_items") or []
        if isinstance(item, dict)
    )
    return (
        len(str(sample.get("chapter_excerpt") or ""))
        + len(str(sample.get("authoritative_context") or ""))
        + len(guards)
        + evidence_chars
    )


def compile_reverification_evidence_window(
    request: dict[str, Any],
    sample: dict[str, Any],
    *,
    max_chars: int = 16000,
    paragraph_radius: int = 1,
) -> dict[str, Any]:
    if max_chars < 500:
        raise ValueError("max_chars must be at least 500")
    if paragraph_radius < 0:
        raise ValueError("paragraph_radius must not be negative")
    scope = str((request.get("route") or {}).get("scope") or "author_intent")
    fragments = _fragments(sample)
    chapter = str(sample.get("chapter_excerpt") or "")
    context = str(sample.get("authoritative_context") or "")
    guards = json.dumps(sample.get("active_author_guards") or {}, ensure_ascii=False, indent=2)
    evidence_items = [item for item in request.get("evidence_items") or [] if isinstance(item, dict)]
    bounded = scope == "full_chapter" and _is_bounded_claim(sample)
    strategy = "bounded_claim_windows" if bounded else "full_scope_deduplicated" if scope == "full_chapter" else "scoped_evidence_windows"

    candidates: list[dict[str, str]] = []
    if guards != "{}":
        candidates.append(
            {
                "kind": "active_author_guards",
                "source": "packet",
                "authority": "author",
                "reason": "active author authority always remains visible",
                "content": guards,
            }
        )

    if bounded:
        local = _paragraph_window(chapter, fragments, radius=paragraph_radius, max_chars=max_chars)
        if local:
            candidates.append(
                {
                    "kind": "claim_evidence_window",
                    "source": "packet.chapter_excerpt",
                    "authority": "manuscript",
                    "reason": "exact finding quotations plus neighboring paragraphs",
                    "content": local,
                }
            )
    elif scope == "full_chapter":
        full_item = next((item for item in evidence_items if item.get("kind") == "full_chapter" and item.get("content")), None)
        full_text = str((full_item or {}).get("content") or chapter)
        if full_text:
            candidates.append(
                {
                    "kind": "full_chapter",
                    "source": str((full_item or {}).get("source") or "packet.chapter_excerpt"),
                    "authority": "manuscript",
                    "reason": "chapter-scale claim requires the chapter once, without packet/escalation duplication",
                    "content": full_text,
                }
            )
    else:
        local = _paragraph_window(chapter, fragments, radius=paragraph_radius, max_chars=max_chars // 2)
        if local:
            candidates.append(
                {
                    "kind": "claim_evidence_window",
                    "source": "packet.chapter_excerpt",
                    "authority": "manuscript",
                    "reason": "exact finding quotations plus neighboring paragraphs",
                    "content": local,
                }
            )
        for item in evidence_items:
            content = str(item.get("content") or "")
            if content:
                candidates.append(
                    {
                        "kind": str(item.get("kind") or "retrieved_evidence"),
                        "source": str(item.get("source") or "escalation"),
                        "authority": str(item.get("authority") or "supporting"),
                        "reason": str(item.get("reason") or "scope-routed evidence"),
                        "content": content,
                    }
                )

    if context:
        context_window = _paragraph_window(context, fragments, radius=paragraph_radius, max_chars=min(4000, max_chars))
        if context_window:
            candidates.append(
                {
                    "kind": "authoritative_context",
                    "source": "packet.authoritative_context",
                    "authority": "canon",
                    "reason": "finding-relevant project context",
                    "content": context_window,
                }
            )

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    remaining = max_chars
    for candidate in candidates:
        content = candidate["content"].strip()
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if not content or digest in seen or remaining <= 0:
            continue
        seen.add(digest)
        included = content[:remaining].rstrip()
        items.append(
            {
                **{key: value for key, value in candidate.items() if key != "content"},
                "sha256": digest,
                "chars": len(content),
                "included_chars": len(included),
                "truncated": len(included) < len(content),
                "content": included,
            }
        )
        remaining -= len(included)

    source_chars = _raw_source_chars(request, sample)
    included_chars = sum(int(item["included_chars"]) for item in items)
    reduction = round((1 - included_chars / source_chars) * 100, 2) if source_chars else 0.0
    full_scope_complete = not (scope == "full_chapter" and not bounded) or any(
        item["kind"] == "full_chapter" and not item["truncated"] for item in items
    )
    return {
        "schema": REVERIFICATION_EVIDENCE_WINDOW_SCHEMA,
        "scope": scope,
        "strategy": strategy,
        "max_chars": max_chars,
        "paragraph_radius": paragraph_radius,
        "source_chars_before": source_chars,
        "included_chars": included_chars,
        "character_reduction_percent": reduction,
        "full_chapter_included": any(item["kind"] == "full_chapter" for item in items),
        "bounded_claim": bounded,
        "scope_complete": full_scope_complete,
        "items": items,
    }


def render_reverification_evidence_window(window: dict[str, Any]) -> str:
    manifest = {**window, "items": [{key: value for key, value in item.items() if key != "content"} for item in window.get("items") or []]}
    sections = ["## Evidence Window Manifest\n```json\n" + json.dumps(manifest, ensure_ascii=False, indent=2) + "\n```"]
    for index, item in enumerate(window.get("items") or [], start=1):
        sections.append(
            f"## Evidence Window {index}: {item['kind']}\n"
            f"Source: {item['source']}. Authority: {item['authority']}. Reason: {item['reason']}.\n\n"
            + str(item.get("content") or "")
        )
    return "\n\n".join(sections)
