from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .agent_exec import parse_runner_receipt, runner_environment
from .agent_project_context import compile_project_context
from .agent_counterevidence_review import COUNTEREVIDENCE_PACKET_SCHEMA


EVIDENCE_ESCALATION_SCHEMA = "fictionops.counterevidence_escalation.v1"
ESCALATED_REVERIFICATION_SCHEMA = "fictionops.escalated_reverification.v1"
ESCALATED_REVERIFICATION_VERDICTS = {"uphold", "withdraw", "still_insufficient"}
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


def escalated_reverification_prompt(request: dict[str, Any], sample: dict[str, Any]) -> str:
    request_id = str(request.get("request_id") or "")
    payload = {
        "schema": "fictionops.escalated_reverification_request.v1",
        "role": "independent-counterevidence-reverifier",
        "task": "rejudge-one-disputed-finding-after-evidence-escalation",
        "request_id": request_id,
    }
    contract = {
        "schema": ESCALATED_REVERIFICATION_SCHEMA,
        "request_id": request_id,
        "verdict": "uphold|withdraw|still_insufficient",
        "evidence": ["exact quotation from supplied material"],
        "reason": "why the escalated evidence changes or preserves the verdict",
        "remaining_gap": "required when verdict is still_insufficient; otherwise empty",
        "confidence": "low|medium|high",
    }
    return "\n\n".join(
        [
            "# FictionOps Escalated Re-verification",
            "## Request\n```json\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```",
            (
                "## Decision Rules\n"
                "Rejudge the original finding only. Use uphold when the escalated evidence materially supports the defect. "
                "Use withdraw when the evidence or an active author guard disproves the defect or shows the proposed repair would violate intent. "
                "Use still_insufficient when the requested evidence remains absent, indirect, or too narrow. "
                "Do not rewrite prose. Do not infer missing facts. Model confidence is not author authority."
            ),
            "## Original Chapter Material\n" + str(sample.get("chapter_excerpt") or ""),
            "## Authoritative Context\n" + str(sample.get("authoritative_context") or ""),
            "## Active Author Guards\n```json\n" + json.dumps(sample.get("active_author_guards") or {}, ensure_ascii=False, indent=2) + "\n```",
            "## Original Reviewer Finding\n```json\n" + json.dumps(sample.get("reviewer_finding") or {}, ensure_ascii=False, indent=2) + "\n```",
            "## Original Verifier Assessment\n```json\n" + json.dumps(sample.get("verifier_assessment") or {}, ensure_ascii=False, indent=2) + "\n```",
            "## Escalation Route\n```json\n" + json.dumps(request.get("route") or {}, ensure_ascii=False, indent=2) + "\n```",
            "## Newly Retrieved Evidence\n```json\n" + json.dumps(request.get("evidence_items") or [], ensure_ascii=False, indent=2) + "\n```",
            "## Output Contract\nReturn exactly one JSON object and no Markdown fence:\n" + json.dumps(contract, ensure_ascii=False, indent=2),
        ]
    ).rstrip() + "\n"


def _parse_reverification(text: str, request_id: str) -> dict[str, Any]:
    cleaned = text.strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("re-verifier did not return a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict) or payload.get("schema") != ESCALATED_REVERIFICATION_SCHEMA:
        raise ValueError(f"re-verifier must declare schema {ESCALATED_REVERIFICATION_SCHEMA}")
    if str(payload.get("request_id") or "") != request_id:
        raise ValueError("re-verifier request_id does not match")
    verdict = str(payload.get("verdict") or "")
    if verdict not in ESCALATED_REVERIFICATION_VERDICTS:
        raise ValueError("re-verifier verdict is invalid")
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
        raise ValueError("re-verifier evidence must be a string array")
    confidence = str(payload.get("confidence") or "")
    if confidence not in {"low", "medium", "high"}:
        raise ValueError("re-verifier confidence is invalid")
    remaining_gap = str(payload.get("remaining_gap") or "").strip()
    if verdict == "still_insufficient" and not remaining_gap:
        raise ValueError("still_insufficient requires remaining_gap")
    return {
        "schema": ESCALATED_REVERIFICATION_SCHEMA,
        "request_id": request_id,
        "verdict": verdict,
        "evidence": evidence,
        "reason": str(payload.get("reason") or "").strip(),
        "remaining_gap": remaining_gap,
        "confidence": confidence,
    }


def _run_reverification_call(prompt: str, runner: list[str], timeout_seconds: int) -> tuple[str, dict[str, Any] | None]:
    completed = subprocess.run(
        runner,
        input=prompt,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=timeout_seconds,
        env=runner_environment(),
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"escalated re-verifier runner failed with {completed.returncode}: {(completed.stderr or completed.stdout)[:600]}")
    if not completed.stdout.strip():
        raise ValueError("escalated re-verifier runner produced empty stdout")
    return completed.stdout, parse_runner_receipt(completed.stderr)


def _repair_prompt(invalid_output: str, request_id: str, error: str) -> str:
    return "\n\n".join(
        [
            "# FictionOps Escalated Re-verification Schema Repair",
            "Repair formatting only. Preserve the intended verdict and reasoning. Return one JSON object and no Markdown fence.",
            f"REQUEST_ID: {request_id}",
            f"PARSE_ERROR: {error}",
            "ALLOWED_VERDICTS: uphold, withdraw, still_insufficient",
            "REQUIRED_SCHEMA: " + ESCALATED_REVERIFICATION_SCHEMA,
            "INVALID_OUTPUT:\n" + invalid_output,
        ]
    ) + "\n"


def apply_reverification_grounding(
    decision: dict[str, Any], request: dict[str, Any], sample: dict[str, Any]
) -> dict[str, Any]:
    sources = [
        str(sample.get("chapter_excerpt") or ""),
        str(sample.get("authoritative_context") or ""),
        json.dumps(sample.get("active_author_guards") or {}, ensure_ascii=False),
    ]
    sources.extend(str(item.get("content") or "") for item in request.get("evidence_items") or [] if isinstance(item, dict))
    evidence = [str(item).strip() for item in decision.get("evidence") or [] if str(item).strip()]
    grounded = [quote for quote in evidence if any(quote in source for source in sources)]
    ungrounded = [quote for quote in evidence if quote not in grounded]
    result = {
        **decision,
        "model_verdict": decision["verdict"],
        "evidence_grounded": bool(grounded),
        "grounded_evidence": grounded,
        "ungrounded_evidence": ungrounded,
        "grounding_override": False,
    }
    if decision["verdict"] in {"uphold", "withdraw"} and not grounded:
        result["verdict"] = "still_insufficient"
        result["remaining_gap"] = "The model resolved the finding without an exact quotation grounded in supplied evidence."
        result["grounding_override"] = True
    return result


def run_escalated_reverification(
    escalation_file: Path,
    packet_file: Path,
    *,
    runner: list[str],
    timeout_seconds: int = 300,
    max_model_calls: int = 12,
) -> dict[str, Any]:
    if not runner:
        raise ValueError("escalated re-verification requires a runner command")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if max_model_calls < 1:
        raise ValueError("max_model_calls must be positive")
    escalation = _read_json(escalation_file)
    packet = _read_json(packet_file)
    if escalation.get("schema") != EVIDENCE_ESCALATION_SCHEMA:
        raise ValueError(f"escalation must declare schema {EVIDENCE_ESCALATION_SCHEMA}")
    if packet.get("schema") != COUNTEREVIDENCE_PACKET_SCHEMA:
        raise ValueError(f"packet must declare schema {COUNTEREVIDENCE_PACKET_SCHEMA}")
    samples = {str(item.get("sample_id") or ""): item for item in packet.get("samples") or [] if isinstance(item, dict)}
    ready = [item for item in escalation.get("requests") or [] if isinstance(item, dict) and item.get("status") == "ready_for_reverification"]
    if len(ready) > max_model_calls:
        raise ValueError("ready request count exceeds max_model_calls before execution")
    results: list[dict[str, Any]] = []
    call_count = 0
    for request in ready:
        request_id = str(request.get("request_id") or "")
        sample_ids = [str(item) for item in request.get("sample_ids") or []]
        if not sample_ids or sample_ids[0] not in samples:
            raise ValueError(f"cannot resolve representative sample for {request_id}")
        prompt = escalated_reverification_prompt(request, samples[sample_ids[0]])
        output, telemetry = _run_reverification_call(prompt, runner, timeout_seconds)
        call_count += 1
        repair_used = False
        repair_telemetry = None
        try:
            decision = _parse_reverification(output, request_id)
        except (json.JSONDecodeError, ValueError) as exc:
            if call_count >= max_model_calls:
                raise ValueError(f"re-verifier output invalid and repair budget exhausted for {request_id}: {exc}") from exc
            repaired, repair_telemetry = _run_reverification_call(_repair_prompt(output, request_id, str(exc)), runner, timeout_seconds)
            call_count += 1
            repair_used = True
            decision = _parse_reverification(repaired, request_id)
        decision = apply_reverification_grounding(decision, request, samples[sample_ids[0]])
        results.append(
            {
                **decision,
                "sample_ids": sample_ids,
                "scope": str((request.get("route") or {}).get("scope") or ""),
                "repair_used": repair_used,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "telemetry": telemetry,
                "repair_telemetry": repair_telemetry,
            }
        )
    verdict_counts = {verdict: sum(item["verdict"] == verdict for item in results) for verdict in sorted(ESCALATED_REVERIFICATION_VERDICTS)}
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cached_input_tokens": 0}
    for result in results:
        for receipt in (result.get("telemetry"), result.get("repair_telemetry")):
            receipt_usage = (receipt or {}).get("usage") or {}
            for key in usage:
                usage[key] += int(receipt_usage.get(key) or 0)
    return {
        "schema": ESCALATED_REVERIFICATION_SCHEMA,
        "escalation": str(escalation_file.resolve()),
        "packet": str(packet_file.resolve()),
        "escalation_sha256": hashlib.sha256(escalation_file.read_bytes()).hexdigest(),
        "packet_sha256": hashlib.sha256(packet_file.read_bytes()).hexdigest(),
        "ready_request_count": len(ready),
        "model_call_count": call_count,
        "verdict_counts": verdict_counts,
        "resolved_after_escalation_count": verdict_counts["uphold"] + verdict_counts["withdraw"],
        "still_insufficient_count": verdict_counts["still_insufficient"],
        "resolution_rate": (verdict_counts["uphold"] + verdict_counts["withdraw"]) / len(ready) if ready else 0.0,
        "usage": usage,
        "results": results,
        "safety": {"edits_manuscript": False, "author_approval_required": True},
    }


def render_escalated_reverification(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported re-verification output format: {output_format}")
    counts = payload["verdict_counts"]
    return "\n".join(
        [
            "# FictionOps Escalated Re-verification",
            "",
            f"- Ready requests: {payload['ready_request_count']}",
            f"- Model calls: {payload['model_call_count']}",
            f"- Verdicts: uphold {counts['uphold']}, withdraw {counts['withdraw']}, still insufficient {counts['still_insufficient']}",
            f"- Resolution rate: {payload['resolution_rate']:.3f}",
            f"- Token usage: {payload['usage']['total_tokens']}",
            "- Manuscript edited: no",
        ]
    ) + "\n"
