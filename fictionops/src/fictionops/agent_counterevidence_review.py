from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

from .agent_research_baseline import load_cases, normalize_category


COUNTEREVIDENCE_PACKET_SCHEMA = "fictionops.counterevidence_blind_packet.v1"
COUNTEREVIDENCE_KEY_SCHEMA = "fictionops.counterevidence_blind_key.v1"
COUNTEREVIDENCE_EVALUATION_SCHEMA = "fictionops.counterevidence_evaluation.v1"
ANNOTATION_DECISIONS = {"uphold", "withdraw", "insufficient"}
HARM_RISKS = {"low", "medium", "high"}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _sample_id(identity: str) -> str:
    return "ce-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:14]


def _annotation_template() -> dict[str, Any]:
    return {
        "decision": None,
        "evidence_grounded": None,
        "repair_harm_risk": None,
        "effort_minutes": None,
        "notes": "",
    }


def _benchmark_lookup(benchmark: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in benchmark.get("rows") or []:
        if not isinstance(row, dict) or str(row.get("mode")) not in {"full", "workflow"}:
            continue
        prompt_id = str(row.get("prompt_id") or "")
        rows.setdefault(prompt_id, row)
    return rows


def _control_class(case: dict[str, Any], issue: dict[str, Any]) -> str:
    if not bool(case.get("expected_issue", bool(case.get("expected_category")))):
        return "preserve"
    accepted = {normalize_category(case.get("expected_category"))}
    accepted.update(normalize_category(item) for item in case.get("accepted_categories") or [])
    return "detect" if normalize_category(issue.get("category")) in accepted else "unevaluable"


def build_counterevidence_from_evidence(
    preservation_file: Path,
    *,
    benchmark_file: Path,
    fixtures_file: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    preservation = _read_json(preservation_file)
    benchmark = _read_json(benchmark_file)
    preservation_sha256 = hashlib.sha256(preservation_file.read_bytes()).hexdigest()
    cases = {str(case.get("prompt_id") or ""): case for case in load_cases(fixtures_file)}
    rows = _benchmark_lookup(benchmark)
    samples: list[dict[str, Any]] = []
    keys: list[dict[str, Any]] = []

    groups = (
        ("initial_negative", preservation.get("cases") or []),
        ("initial_positive", preservation.get("positive_cases") or []),
        ("guard_registry", preservation.get("author_guard_registry_dogfood") or []),
    )
    for group_name, entries in groups:
        for entry_index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            prompt_id = str(entry.get("prompt_id") or "")
            case = cases.get(prompt_id)
            row = rows.get(prompt_id)
            if case is None or row is None:
                raise ValueError(f"cannot resolve benchmark sources for prompt_id {prompt_id!r}")
            issues = [item for item in (row.get("review") or {}).get("issues") or [] if isinstance(item, dict)]
            author_guards = entry.get("author_guards") if isinstance(entry.get("author_guards"), dict) else {}
            for decision in entry.get("decisions") or []:
                if not isinstance(decision, dict) or decision.get("verdict") != "needs_counterevidence":
                    continue
                issue_index = int(decision.get("issue_index", -1))
                if issue_index < 0 or issue_index >= len(issues):
                    raise ValueError(f"invalid issue_index {issue_index} for {prompt_id}")
                issue = issues[issue_index]
                identity = f"{preservation_sha256}|{group_name}|{entry_index}|{prompt_id}|{issue_index}"
                sample_id = _sample_id(identity)
                samples.append(
                    {
                        "sample_id": sample_id,
                        "source_scope": "benchmark_excerpt",
                        "chapter_excerpt": str(case.get("chapter_excerpt") or ""),
                        "authoritative_context": str(case.get("project_context") or ""),
                        "supplied_preservation_context": str(case.get("false_positive_guard") or ""),
                        "active_author_guards": author_guards,
                        "reviewer_finding": issue,
                        "verifier_assessment": {
                            "evidence": decision.get("evidence") or [],
                            "reason": str(decision.get("reason") or ""),
                            "guard_ids": decision.get("guard_ids") or [],
                        },
                        "annotation": _annotation_template(),
                    }
                )
                keys.append(
                    {
                        "sample_id": sample_id,
                        "source_group": group_name,
                        "prompt_id": prompt_id,
                        "case_id": str(case.get("case_id") or ""),
                        "issue_index": issue_index,
                        "control_class": _control_class(case, issue),
                        "expected_issue": bool(case.get("expected_issue", bool(case.get("expected_category")))),
                        "condition": str(row.get("mode") or ""),
                    }
                )
    return _finish_artifacts(samples, keys, source=str(preservation_file.resolve()))


def build_counterevidence_from_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    run_dir = run_dir.expanduser().resolve()
    review = _read_json(run_dir / "comprehensive_review.json")
    verification = _read_json(run_dir / "preservation_verification.json")
    issues = [item for item in review.get("reviewer_issues") or review.get("issues") or [] if isinstance(item, dict)]
    chapter = (run_dir / "source_chapter.md").read_text(encoding="utf-8")
    context_file = run_dir / "project_context.md"
    context = context_file.read_text(encoding="utf-8") if context_file.is_file() else ""
    guards_file = run_dir / "author_guards.json"
    guards_payload = _read_json(guards_file) if guards_file.is_file() else {"guards": []}
    active_guards = {
        str(item.get("id")): str(item.get("statement") or "")
        for item in guards_payload.get("guards") or []
        if isinstance(item, dict) and item.get("status") == "active"
    }
    samples: list[dict[str, Any]] = []
    keys: list[dict[str, Any]] = []
    for decision in verification.get("decisions") or []:
        if not isinstance(decision, dict) or decision.get("verdict") != "needs_counterevidence":
            continue
        issue_index = int(decision.get("issue_index", -1))
        if issue_index < 0 or issue_index >= len(issues):
            raise ValueError(f"invalid issue_index {issue_index} in revision run")
        sample_id = _sample_id(f"{run_dir}|{issue_index}")
        samples.append(
            {
                "sample_id": sample_id,
                "source_scope": "full_chapter",
                "chapter_excerpt": chapter,
                "authoritative_context": context,
                "supplied_preservation_context": "",
                "active_author_guards": active_guards,
                "reviewer_finding": issues[issue_index],
                "verifier_assessment": {
                    "evidence": decision.get("evidence") or [],
                    "reason": str(decision.get("reason") or ""),
                    "guard_ids": decision.get("guard_ids") or [],
                },
                "annotation": _annotation_template(),
            }
        )
        keys.append(
            {
                "sample_id": sample_id,
                "source_group": "revision_run",
                "issue_index": issue_index,
                "control_class": "unevaluable",
                "run_dir": str(run_dir),
            }
        )
    return _finish_artifacts(samples, keys, source=str(run_dir))


def _finish_artifacts(
    samples: list[dict[str, Any]], keys: list[dict[str, Any]], *, source: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    samples.sort(key=lambda item: hashlib.sha256(str(item["sample_id"]).encode("utf-8")).hexdigest())
    keys.sort(key=lambda item: str(item["sample_id"]))
    packet = {
        "schema": COUNTEREVIDENCE_PACKET_SCHEMA,
        "instructions": {
            "decision": "uphold = finding should reach the reviser; withdraw = preserve the text; insufficient = human also needs more evidence.",
            "evidence_grounded": "Whether the finding is supported by the supplied excerpt and authoritative context.",
            "repair_harm_risk": "Risk that acting on the finding would damage intended characterization, ambiguity, voice, or rhythm: low, medium, or high.",
            "privacy": "Do not inspect the separately stored key while annotating.",
        },
        "sample_count": len(samples),
        "samples": samples,
    }
    key = {
        "schema": COUNTEREVIDENCE_KEY_SCHEMA,
        "source": source,
        "sample_count": len(keys),
        "samples": keys,
    }
    return packet, key


def evaluate_counterevidence(packet_file: Path, key_file: Path) -> dict[str, Any]:
    packet = _read_json(packet_file)
    key = _read_json(key_file)
    if packet.get("schema") != COUNTEREVIDENCE_PACKET_SCHEMA:
        raise ValueError(f"packet must declare schema {COUNTEREVIDENCE_PACKET_SCHEMA}")
    if key.get("schema") != COUNTEREVIDENCE_KEY_SCHEMA:
        raise ValueError(f"key must declare schema {COUNTEREVIDENCE_KEY_SCHEMA}")
    samples = packet.get("samples") or []
    key_rows = key.get("samples") or []
    sample_ids = [str(item.get("sample_id") or "") for item in samples if isinstance(item, dict)]
    key_ids = [str(item.get("sample_id") or "") for item in key_rows if isinstance(item, dict)]
    if len(sample_ids) != len(set(sample_ids)) or len(key_ids) != len(set(key_ids)):
        raise ValueError("packet and key must not contain duplicate sample ids")
    if set(sample_ids) != set(key_ids):
        raise ValueError("packet and key sample ids do not match")
    keys = {str(item["sample_id"]): item for item in key_rows}
    rows: list[dict[str, Any]] = []
    efforts: list[float] = []
    for sample in samples:
        annotation = sample.get("annotation") if isinstance(sample.get("annotation"), dict) else {}
        decision = annotation.get("decision")
        grounded = annotation.get("evidence_grounded")
        harm = annotation.get("repair_harm_risk")
        effort = annotation.get("effort_minutes")
        if decision not in ANNOTATION_DECISIONS:
            raise ValueError(f"sample {sample.get('sample_id')} needs a valid annotation decision")
        if not isinstance(grounded, bool):
            raise ValueError(f"sample {sample.get('sample_id')} needs evidence_grounded true or false")
        if harm not in HARM_RISKS:
            raise ValueError(f"sample {sample.get('sample_id')} needs repair_harm_risk low, medium, or high")
        if isinstance(effort, bool) or not isinstance(effort, (int, float)) or effort < 0:
            raise ValueError(f"sample {sample.get('sample_id')} needs non-negative effort_minutes")
        efforts.append(float(effort))
        control = str(keys[str(sample["sample_id"])].get("control_class") or "unevaluable")
        outcome = "unevaluable"
        if control == "detect" and decision == "uphold":
            outcome = "expected_detect_upheld"
        elif control == "detect" and decision == "withdraw":
            outcome = "detect_label_challenge"
        elif control == "preserve" and decision == "uphold":
            outcome = "preserve_label_challenge"
        elif control == "preserve" and decision == "withdraw":
            outcome = "preserve_confirmed"
        elif control in {"detect", "preserve"}:
            outcome = "unresolved_control"
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "decision": decision,
                "control_class": control,
                "outcome": outcome,
                "evidence_grounded": grounded,
                "repair_harm_risk": harm,
                "effort_minutes": float(effort),
            }
        )
    counts = {decision: sum(row["decision"] == decision for row in rows) for decision in sorted(ANNOTATION_DECISIONS)}
    control_summary = {
        name: sum(row["outcome"] == name for row in rows)
        for name in (
            "expected_detect_upheld",
            "detect_label_challenge",
            "preserve_label_challenge",
            "preserve_confirmed",
            "unresolved_control",
        )
    }
    resolved_controls = sum(
        control_summary[name]
        for name in ("expected_detect_upheld", "detect_label_challenge", "preserve_label_challenge", "preserve_confirmed")
    )
    aligned_controls = control_summary["expected_detect_upheld"] + control_summary["preserve_confirmed"]
    return {
        "schema": COUNTEREVIDENCE_EVALUATION_SCHEMA,
        "packet": str(packet_file.resolve()),
        "sample_count": len(rows),
        "decision_counts": counts,
        "resolved_rate": (counts["uphold"] + counts["withdraw"]) / len(rows) if rows else 0.0,
        "grounded_rate": sum(row["evidence_grounded"] for row in rows) / len(rows) if rows else 0.0,
        "high_harm_risk_count": sum(row["repair_harm_risk"] == "high" for row in rows),
        "total_effort_minutes": sum(efforts),
        "mean_effort_minutes": statistics.fmean(efforts) if efforts else 0.0,
        "median_effort_minutes": statistics.median(efforts) if efforts else 0.0,
        "control_summary": control_summary,
        "control_agreement_rate": aligned_controls / resolved_controls if resolved_controls else None,
        "control_label_scope": "Case-level benchmark labels inherited by issue samples; disagreements are label challenges, not adjudicator errors.",
        "rows": rows,
    }


def render_counterevidence_evaluation(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported counterevidence output format: {output_format}")
    counts = payload["decision_counts"]
    controls = payload["control_summary"]
    agreement = payload["control_agreement_rate"]
    return "\n".join(
        [
            "# FictionOps Counterevidence Evaluation",
            "",
            f"- Samples: {payload['sample_count']}",
            f"- Decisions: uphold {counts['uphold']}, withdraw {counts['withdraw']}, insufficient {counts['insufficient']}",
            f"- Resolved rate: {payload['resolved_rate']:.3f}",
            f"- Grounded rate: {payload['grounded_rate']:.3f}",
            f"- High repair-harm risk: {payload['high_harm_risk_count']}",
            f"- Human effort: {payload['total_effort_minutes']:.1f} minutes total, {payload['median_effort_minutes']:.1f} median",
            f"- Case-control alignment: expected-detect upheld {controls['expected_detect_upheld']}, preserve confirmed {controls['preserve_confirmed']}, label challenges {controls['detect_label_challenge'] + controls['preserve_label_challenge']}, unresolved {controls['unresolved_control']}",
            f"- Resolved control agreement: {agreement:.3f}" if agreement is not None else "- Resolved control agreement: n/a",
            f"- Label scope: {payload['control_label_scope']}",
        ]
    ) + "\n"
