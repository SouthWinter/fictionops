from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .agent_evidence_escalation import (
    _parse_reverification,
    _run_reverification_call,
    apply_reverification_grounding,
    escalated_reverification_prompt,
)
from .agent_evidence_window import (
    REVERIFICATION_EVIDENCE_WINDOW_SCHEMA,
    compile_reverification_evidence_window,
)


EVIDENCE_WINDOW_BENCHMARK_SCHEMA = "fictionops.evidence_window_benchmark.v1"
EVIDENCE_WINDOW_FIXTURE_SCHEMA = "fictionops.evidence_window_benchmark_cases.v1"
EVIDENCE_WINDOW_CONDITIONS = ("full_context", "window")


def load_evidence_window_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != EVIDENCE_WINDOW_FIXTURE_SCHEMA:
        raise ValueError(f"fixtures must declare schema {EVIDENCE_WINDOW_FIXTURE_SCHEMA}")
    cases = [item for item in payload.get("cases") or [] if isinstance(item, dict)]
    if not cases:
        raise ValueError("evidence-window fixtures must contain at least one case")
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("case_id") or "")
        if not case_id or case_id in seen:
            raise ValueError("evidence-window case_id values must be unique and non-empty")
        seen.add(case_id)
        if str(case.get("expected_verdict") or "") not in {"uphold", "withdraw", "still_insufficient"}:
            raise ValueError(f"invalid expected_verdict for {case_id}")
        if not isinstance(case.get("sample"), dict) or not isinstance(case.get("request"), dict):
            raise ValueError(f"case {case_id} requires sample and request objects")
    return cases


def build_full_context_window(request: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        ("packet_chapter", "packet.chapter_excerpt", "manuscript", str(sample.get("chapter_excerpt") or "")),
        ("packet_context", "packet.authoritative_context", "canon", str(sample.get("authoritative_context") or "")),
        (
            "packet_author_guards",
            "packet.active_author_guards",
            "author",
            json.dumps(sample.get("active_author_guards") or {}, ensure_ascii=False, indent=2),
        ),
    ]
    for index, item in enumerate(request.get("evidence_items") or [], start=1):
        if isinstance(item, dict):
            candidates.append(
                (
                    str(item.get("kind") or f"retrieved_{index}"),
                    str(item.get("source") or "escalation"),
                    str(item.get("authority") or "supporting"),
                    str(item.get("content") or ""),
                )
            )
    items: list[dict[str, Any]] = []
    for kind, source, authority, content in candidates:
        if not content:
            continue
        items.append(
            {
                "kind": kind,
                "source": source,
                "authority": authority,
                "reason": "full-context benchmark condition",
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "chars": len(content),
                "included_chars": len(content),
                "truncated": False,
                "content": content,
            }
        )
    included = sum(int(item["included_chars"]) for item in items)
    return {
        "schema": REVERIFICATION_EVIDENCE_WINDOW_SCHEMA,
        "scope": str((request.get("route") or {}).get("scope") or ""),
        "strategy": "full_context_control",
        "max_chars": included,
        "paragraph_radius": None,
        "source_chars_before": included,
        "included_chars": included,
        "character_reduction_percent": 0.0,
        "full_chapter_included": bool(sample.get("chapter_excerpt")),
        "bounded_claim": False,
        "scope_complete": True,
        "items": items,
    }


def _receipt_usage(receipt: dict[str, Any] | None) -> dict[str, int]:
    usage = (receipt or {}).get("usage") or {}
    return {
        key: int(usage.get(key) or 0)
        for key in ("input_tokens", "output_tokens", "total_tokens", "cached_input_tokens")
    }


def _aggregate(rows: list[dict[str, Any]], conditions: list[str]) -> dict[str, Any]:
    aggregate: dict[str, Any] = {}
    for condition in conditions:
        selected = [row for row in rows if row["condition"] == condition]
        aggregate[condition] = {
            "samples": len(selected),
            "expected_verdict_accuracy": sum(bool(row["expected_verdict_match"]) for row in selected) / len(selected)
            if selected
            else 0.0,
            "grounded_resolution_rate": sum(bool(row["grounded_resolution"]) for row in selected) / len(selected)
            if selected
            else 0.0,
            "evidence_recall_rate": sum(bool(row["required_evidence_recalled"]) for row in selected) / len(selected)
            if selected
            else 0.0,
            "still_insufficient_rate": sum(row["effective_verdict"] == "still_insufficient" for row in selected) / len(selected)
            if selected
            else 0.0,
            "input_tokens": sum(int(row["usage"]["input_tokens"]) for row in selected),
            "output_tokens": sum(int(row["usage"]["output_tokens"]) for row in selected),
            "total_tokens": sum(int(row["usage"]["total_tokens"]) for row in selected),
            "prompt_chars": sum(int(row["prompt_chars"]) for row in selected),
            "evidence_chars": sum(int(row["evidence_window"]["included_chars"]) for row in selected),
        }
    return aggregate


def _paired_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["case_id"]), int(row["run_index"])), {})[str(row["condition"])] = row
    pairs = [group for group in grouped.values() if all(condition in group for condition in EVIDENCE_WINDOW_CONDITIONS)]
    full_input = sum(group["full_context"]["usage"]["input_tokens"] for group in pairs)
    window_input = sum(group["window"]["usage"]["input_tokens"] for group in pairs)
    full_chars = sum(group["full_context"]["evidence_window"]["included_chars"] for group in pairs)
    window_chars = sum(group["window"]["evidence_window"]["included_chars"] for group in pairs)
    by_scope: dict[str, dict[str, Any]] = {}
    for group in pairs:
        full, window = group["full_context"], group["window"]
        scope = str(window["scope"])
        item = by_scope.setdefault(scope, {"pairs": 0, "verdict_agreements": 0, "window_correct": 0, "input_tokens_before": 0, "input_tokens_after": 0})
        item["pairs"] += 1
        item["verdict_agreements"] += full["effective_verdict"] == window["effective_verdict"]
        item["window_correct"] += bool(window["expected_verdict_match"])
        item["input_tokens_before"] += int(full["usage"]["input_tokens"])
        item["input_tokens_after"] += int(window["usage"]["input_tokens"])
    for item in by_scope.values():
        item["verdict_agreement_rate"] = item.pop("verdict_agreements") / item["pairs"]
        item["window_accuracy"] = item.pop("window_correct") / item["pairs"]
        before, after = item["input_tokens_before"], item["input_tokens_after"]
        item["input_token_reduction_percent"] = round((1 - after / before) * 100, 2) if before else 0.0
    return {
        "pair_count": len(pairs),
        "verdict_agreement_rate": sum(
            group["full_context"]["effective_verdict"] == group["window"]["effective_verdict"] for group in pairs
        )
        / len(pairs)
        if pairs
        else 0.0,
        "window_expected_verdict_accuracy": sum(bool(group["window"]["expected_verdict_match"]) for group in pairs) / len(pairs)
        if pairs
        else 0.0,
        "window_grounded_resolution_rate": sum(bool(group["window"]["grounded_resolution"]) for group in pairs) / len(pairs)
        if pairs
        else 0.0,
        "input_tokens_before": full_input,
        "input_tokens_after": window_input,
        "input_token_reduction_percent": round((1 - window_input / full_input) * 100, 2) if full_input else 0.0,
        "evidence_chars_before": full_chars,
        "evidence_chars_after": window_chars,
        "evidence_character_reduction_percent": round((1 - window_chars / full_chars) * 100, 2) if full_chars else 0.0,
        "by_scope": by_scope,
    }


def run_evidence_window_benchmark(
    fixtures: Path,
    *,
    runner: list[str],
    conditions: list[str] | None = None,
    runs: int = 1,
    timeout_seconds: int = 300,
    max_evidence_chars: int = 16000,
) -> dict[str, Any]:
    if not runner:
        raise ValueError("evidence-window benchmark requires a runner command")
    selected_conditions = conditions or list(EVIDENCE_WINDOW_CONDITIONS)
    invalid = [condition for condition in selected_conditions if condition not in EVIDENCE_WINDOW_CONDITIONS]
    if invalid:
        raise ValueError("unsupported evidence-window conditions: " + ", ".join(invalid))
    if runs < 1 or runs > 20:
        raise ValueError("benchmark runs must be between 1 and 20")
    rows: list[dict[str, Any]] = []
    for case in load_evidence_window_cases(fixtures):
        case_id = str(case["case_id"])
        sample = dict(case["sample"])
        request = dict(case["request"])
        request["request_id"] = str(request.get("request_id") or f"ew-{case_id}")
        request.setdefault("sample_ids", [case_id])
        expected = str(case["expected_verdict"])
        required = [str(item) for item in case.get("required_evidence_any") or [] if str(item)]
        for condition in selected_conditions:
            for run_index in range(1, runs + 1):
                window = (
                    build_full_context_window(request, sample)
                    if condition == "full_context"
                    else compile_reverification_evidence_window(request, sample, max_chars=max_evidence_chars)
                )
                if not window["scope_complete"]:
                    raise ValueError(f"evidence window is incomplete for {case_id}; increase max_evidence_chars")
                prompt = escalated_reverification_prompt(request, sample, window)
                stdout, telemetry = _run_reverification_call(prompt, runner, timeout_seconds)
                decision = _parse_reverification(stdout, str(request["request_id"]))
                effective = apply_reverification_grounding(decision, request, sample, window)
                visible = "\n".join(str(item.get("content") or "") for item in window["items"])
                row = {
                    "case_id": case_id,
                    "scope": str(case.get("scope") or window.get("scope") or ""),
                    "condition": condition,
                    "run_index": run_index,
                    "expected_verdict": expected,
                    "model_verdict": effective["model_verdict"],
                    "effective_verdict": effective["verdict"],
                    "expected_verdict_match": effective["verdict"] == expected,
                    "evidence_grounded": bool(effective["evidence_grounded"]),
                    "grounded_resolution": effective["verdict"] in {"uphold", "withdraw"} and bool(effective["evidence_grounded"]),
                    "required_evidence_recalled": not required or any(fragment in visible for fragment in required),
                    "prompt_chars": len(prompt),
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "evidence_window": {key: value for key, value in window.items() if key != "items"},
                    "usage": _receipt_usage(telemetry),
                    "telemetry": telemetry,
                    "decision": effective,
                }
                rows.append(row)
    aggregate = _aggregate(rows, selected_conditions)
    return {
        "schema": EVIDENCE_WINDOW_BENCHMARK_SCHEMA,
        "fixtures": str(fixtures.resolve()),
        "fixtures_sha256": hashlib.sha256(fixtures.read_bytes()).hexdigest(),
        "conditions": selected_conditions,
        "runs_per_case": runs,
        "case_count": len(load_evidence_window_cases(fixtures)),
        "model_call_count": len(rows),
        "aggregate": aggregate,
        "paired": _paired_metrics(rows) if all(condition in selected_conditions for condition in EVIDENCE_WINDOW_CONDITIONS) else None,
        "rows": rows,
        "safety": {"edits_manuscript": False, "expected_verdict_sent_to_model": False},
    }


def render_evidence_window_benchmark(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported evidence-window benchmark format: {output_format}")
    lines = [
        "# FictionOps Evidence-window Benchmark",
        "",
        f"- Cases: {payload['case_count']}",
        f"- Runs per case: {payload['runs_per_case']}",
        f"- Model calls: {payload['model_call_count']}",
        "",
        "| Condition | Accuracy | Grounded resolutions | Evidence recall | Input tokens | Evidence chars |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in payload["conditions"]:
        item = payload["aggregate"][condition]
        lines.append(
            f"| `{condition}` | {item['expected_verdict_accuracy']:.3f} | {item['grounded_resolution_rate']:.3f} | "
            f"{item['evidence_recall_rate']:.3f} | {item['input_tokens']} | {item['evidence_chars']} |"
        )
    paired = payload.get("paired")
    if paired:
        lines.extend(
            [
                "",
                f"- Paired verdict agreement: {paired['verdict_agreement_rate']:.3f}",
                f"- Window expected-verdict accuracy: {paired['window_expected_verdict_accuracy']:.3f}",
                f"- Input-token reduction: {paired['input_token_reduction_percent']:.2f}%",
                f"- Evidence-character reduction: {paired['evidence_character_reduction_percent']:.2f}%",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
