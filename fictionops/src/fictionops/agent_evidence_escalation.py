from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .agent_project_context import compile_project_context
from .agent_counterevidence_review import COUNTEREVIDENCE_PACKET_SCHEMA


EVIDENCE_ESCALATION_SCHEMA = "fictionops.counterevidence_escalation.v1"
EVIDENCE_SCOPES = {
    "full_chapter",
    "adjacent_paragraphs",
    "knowledge_source",
    "character_memory",
    "author_intent",
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _finding_text(sample: dict[str, Any]) -> str:
    finding = sample.get("reviewer_finding") if isinstance(sample.get("reviewer_finding"), dict) else {}
    verifier = sample.get("verifier_assessment") if isinstance(sample.get("verifier_assessment"), dict) else {}
    return "\n".join(
        [
            str(finding.get("category") or ""),
            str(finding.get("evidence") or ""),
            str(finding.get("problem") or ""),
            str(finding.get("suggested_action") or ""),
            str(verifier.get("reason") or ""),
        ]
    )


def classify_evidence_scope(sample: dict[str, Any]) -> dict[str, Any]:
    text = _finding_text(sample).casefold()
    routes = (
        (
            "full_chapter",
            r"chapter function|within the chapter|narrative arc|climax|transition|pause|filler|momentum|forward momentum|pacing|full chapter|foreshadow|prior or future|echo|larger narrative thread|全章|章节(?:功能|结构|节奏)|高潮|过渡|停顿|推进|填充|伏笔|回声|前文|后文",
            ["full_chapter", "chapter_engine", "outline"],
            "The claim evaluates a chapter-level function or narrative echo and needs evidence at the same structural scale.",
        ),
        (
            "knowledge_source",
            r"information bound|knowledge|how .* know|access to|inventory|source of (?:the )?information|信息(?:来源|边界)|如何(?:知道|获知)|库存|仓数|三仓",
            ["character_memory", "canon_boundary", "adjacent_chapters"],
            "The claim depends on what the character could know and where that information came from.",
        ),
        (
            "adjacent_paragraphs",
            r"adjacent|paragraphs?|three consecutive|across three|repetition|rhythm|parallelism|syntactic|相邻|连续.{0,8}段|跨段|重复|排比|句法|节奏",
            ["adjacent_paragraphs"],
            "The claim compares prose across paragraph boundaries and needs the neighboring source text.",
        ),
        (
            "character_memory",
            r"character|relationship|tone|precocious|age|father-daughter|人物|性格|关系|语气|年龄|父女",
            ["character_memory", "author_guards"],
            "The claim depends on a stable character or relationship model.",
        ),
    )
    for scope, pattern, requested, rationale in routes:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return {"scope": scope, "requested_sources": requested, "rationale": rationale}
    return {
        "scope": "author_intent",
        "requested_sources": ["author_guards"],
        "rationale": "No deterministic external evidence route is strong enough; retain the author boundary.",
    }


def _finding_fingerprint(sample: dict[str, Any]) -> str:
    finding = sample.get("reviewer_finding") if isinstance(sample.get("reviewer_finding"), dict) else {}
    normalized = "|".join(
        re.sub(r"\s+", " ", str(finding.get(key) or "")).strip().casefold()
        for key in ("category", "evidence", "problem", "suggested_action")
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _bounded_item(kind: str, source: str, authority: str, reason: str, content: str, limit: int) -> dict[str, Any]:
    bounded = content[:limit]
    return {
        "kind": kind,
        "source": source,
        "authority": authority,
        "reason": reason,
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "chars": len(content),
        "included_chars": len(bounded),
        "truncated": len(content) > len(bounded),
        "content": bounded,
    }


def _evidence_fragments(sample: dict[str, Any]) -> list[str]:
    finding = sample.get("reviewer_finding") if isinstance(sample.get("reviewer_finding"), dict) else {}
    verifier = sample.get("verifier_assessment") if isinstance(sample.get("verifier_assessment"), dict) else {}
    values: list[Any] = []
    evidence = finding.get("evidence")
    values.extend(evidence if isinstance(evidence, list) else [evidence])
    values.extend(verifier.get("evidence") or [])
    fragments: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and len(text) >= 4:
            fragments.append(text)
        fragments.extend(
            part.strip()
            for groups in re.findall(r"'([^']+)'|\"([^\"]+)\"|‘([^’]+)’|“([^”]+)”", text)
            for part in groups
            if part.strip()
        )
    return list(dict.fromkeys(fragments))


def _adjacent_window(chapter: str, sample: dict[str, Any], radius: int = 2) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", chapter) if part.strip()]
    fragments = _evidence_fragments(sample)
    index = next(
        (
            paragraph_index
            for paragraph_index, paragraph in enumerate(paragraphs)
            if any(fragment in paragraph or fragment[:24] in paragraph for fragment in fragments if len(fragment) >= 4)
        ),
        None,
    )
    if index is None:
        return ""
    start, end = max(0, index - radius), min(len(paragraphs), index + radius + 1)
    return "\n\n".join(paragraphs[start:end])


def _retrieve_project_context(chapter_file: Path, sample: dict[str, Any], max_chars: int) -> list[dict[str, Any]]:
    query = _finding_text(sample)
    bundle = compile_project_context(
        chapter_file,
        task="counterevidence escalation for character knowledge and canon",
        source_text=query,
        max_files=8,
        max_chars_per_file=min(6000, max_chars),
        max_total_chars=max_chars,
    )
    preferred = [item for item in bundle.items if item.role in {"character memory", "canon boundary", "adjacent chapter"}]
    selected = preferred or bundle.items[:3]
    return [
        {
            "kind": item.role.replace(" ", "_"),
            "source": item.path,
            "authority": item.authority,
            "reason": item.reason,
            "sha256": item.sha256,
            "chars": item.chars,
            "included_chars": item.included_chars,
            "truncated": item.truncated,
            "content": item.content,
        }
        for item in selected
    ]


def build_evidence_escalation(
    packet_file: Path,
    *,
    chapter_file: Path | None = None,
    max_chars_per_item: int = 20000,
) -> dict[str, Any]:
    if max_chars_per_item < 100:
        raise ValueError("max_chars_per_item must be at least 100")
    packet = _read_json(packet_file)
    if packet.get("schema") != COUNTEREVIDENCE_PACKET_SCHEMA:
        raise ValueError(f"packet must declare schema {COUNTEREVIDENCE_PACKET_SCHEMA}")
    samples = [item for item in packet.get("samples") or [] if isinstance(item, dict)]
    annotated = [
        item
        for item in samples
        if isinstance(item.get("annotation"), dict) and item["annotation"].get("decision") == "insufficient"
    ]
    selected = annotated or [
        item
        for item in samples
        if not isinstance(item.get("annotation"), dict) or item["annotation"].get("decision") is None
    ]
    groups: dict[str, list[dict[str, Any]]] = {}
    for sample in selected:
        groups.setdefault(_finding_fingerprint(sample), []).append(sample)

    resolved_chapter = chapter_file.expanduser().resolve() if chapter_file else None
    if resolved_chapter and (not resolved_chapter.is_file() or resolved_chapter.suffix.lower() != ".md"):
        raise ValueError("chapter_file must be an existing Markdown file")
    chapter = resolved_chapter.read_text(encoding="utf-8") if resolved_chapter else ""
    requests: list[dict[str, Any]] = []
    for fingerprint, members in sorted(groups.items(), key=lambda item: item[0]):
        representative = members[0]
        route = classify_evidence_scope(representative)
        evidence_items: list[dict[str, Any]] = []
        if route["scope"] == "full_chapter":
            source_scope = str(representative.get("source_scope") or "")
            if chapter:
                evidence_items.append(_bounded_item("full_chapter", str(resolved_chapter), "manuscript", "chapter-scale claim", chapter, max_chars_per_item))
            elif source_scope == "full_chapter":
                evidence_items.append(_bounded_item("full_chapter", "packet", "manuscript", "packet already contains the full chapter", str(representative.get("chapter_excerpt") or ""), max_chars_per_item))
        elif route["scope"] == "adjacent_paragraphs" and chapter:
            window = _adjacent_window(chapter, representative)
            if window:
                evidence_items.append(_bounded_item("adjacent_paragraphs", str(resolved_chapter), "manuscript", "evidence-centered paragraph window", window, max_chars_per_item))
        elif route["scope"] in {"knowledge_source", "character_memory"} and resolved_chapter:
            evidence_items.extend(_retrieve_project_context(resolved_chapter, representative, max_chars_per_item))
        elif route["scope"] == "author_intent":
            guards = representative.get("active_author_guards") if isinstance(representative.get("active_author_guards"), dict) else {}
            if guards:
                evidence_items.append(_bounded_item("author_guards", "packet", "author", "active author authority", json.dumps(guards, ensure_ascii=False, indent=2), max_chars_per_item))
        status = "ready_for_reverification" if evidence_items else "needs_source"
        requests.append(
            {
                "request_id": "er-" + fingerprint[:14],
                "sample_ids": [str(item.get("sample_id") or "") for item in members],
                "deduplicated_count": len(members),
                "route": route,
                "status": status,
                "evidence_items": evidence_items,
                "remaining_gap": "" if evidence_items else "The requested evidence source was not supplied or could not be located.",
                "next_action": "reverify_with_escalated_evidence" if evidence_items else "request_source_before_human_review",
            }
        )
    scope_counts = {scope: sum(item["route"]["scope"] == scope for item in requests) for scope in sorted(EVIDENCE_SCOPES)}
    return {
        "schema": EVIDENCE_ESCALATION_SCHEMA,
        "packet": str(packet_file.resolve()),
        "selected_sample_count": len(selected),
        "request_count": len(requests),
        "duplicates_collapsed": len(selected) - len(requests),
        "ready_for_reverification_count": sum(item["status"] == "ready_for_reverification" for item in requests),
        "needs_source_count": sum(item["status"] == "needs_source" for item in requests),
        "scope_counts": scope_counts,
        "requests": requests,
    }


def render_evidence_escalation(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported evidence escalation output format: {output_format}")
    lines = [
        "# FictionOps Evidence Escalation",
        "",
        f"- Selected findings: {payload['selected_sample_count']}",
        f"- Deduplicated requests: {payload['request_count']}",
        f"- Duplicates collapsed: {payload['duplicates_collapsed']}",
        f"- Ready for reverification: {payload['ready_for_reverification_count']}",
        f"- Missing source: {payload['needs_source_count']}",
        "",
        "| Request | Scope | Samples | Status | Next action |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in payload["requests"]:
        lines.append(
            f"| `{item['request_id']}` | `{item['route']['scope']}` | {len(item['sample_ids'])} | `{item['status']}` | `{item['next_action']}` |"
        )
    return "\n".join(lines).rstrip() + "\n"
