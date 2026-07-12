from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from .agent_budget import ModelBudgetExceeded, ModelExecutionBudget, start_model_budget
from .agent_exec import parse_runner_receipt
from .agent_session_control import cancel_agent_session, validate_checkpoint_for_resume, write_agent_checkpoint
from .agent_story_reasoning import deterministic_story_audit, review_evidence_grounding_issues


FAILURE_LAB_SCHEMA = "fictionops.agent_failure_lab.v1"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _session_fixture(root: Path, name: str) -> tuple[Path, Path, Path]:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    source = root / f"{name}.md"
    engine = root / f"{name}.engine.md"
    artifact = run_dir / "artifact.json"
    source.write_text("# Protected chapter\n\nOne stable event.\n", encoding="utf-8")
    engine.write_text("# Engine\n\n- change: one stable event\n", encoding="utf-8")
    artifact.write_text('{"state":"stable"}\n', encoding="utf-8")
    session = {
        "session_id": name,
        "workflow": "chapter_write",
        "state": "context_ready",
        "source_file": str(source.resolve()),
        "source_sha256": hashlib.sha256(source.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
        "engine_file": str(engine.resolve()),
        "engine_sha256": hashlib.sha256(engine.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
    }
    (run_dir / "session.json").write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    write_agent_checkpoint(run_dir, phase="context_ready", next_action="test_resume", artifacts=[artifact])
    return run_dir, source, artifact


def _scenario(
    scenario_id: str,
    expected_boundary: str,
    execute: Callable[[], tuple[bool, bool | None, dict[str, Any]]],
    protected: Path,
) -> dict[str, Any]:
    before = _hash(protected)
    detected, recovered, details = execute()
    return {
        "scenario_id": scenario_id,
        "expected_boundary": expected_boundary,
        "detected": detected,
        "recovery_succeeded": recovered,
        "protected_hash_unchanged": _hash(protected) == before,
        "details": details,
    }


def run_failure_lab() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="fictionops-failure-lab-") as tmp:
        root = Path(tmp)
        protected = root / "protected_canon.md"
        protected.write_text("# Canon\n\nThis file must never change.\n", encoding="utf-8")
        scenarios: list[dict[str, Any]] = []

        def clean_error(exc: Exception) -> str:
            return str(exc).replace(str(root.resolve()), "<failure-lab-root>")

        def stale_source() -> tuple[bool, None, dict[str, Any]]:
            run_dir, source, _ = _session_fixture(root, "stale_source")
            source.write_text(source.read_text(encoding="utf-8") + "Concurrent author edit.\n", encoding="utf-8")
            try:
                validate_checkpoint_for_resume(run_dir)
            except RuntimeError as exc:
                return True, None, {"error": clean_error(exc), "detection_point": "resume_preflight"}
            return False, None, {"detection_point": "missed"}

        scenarios.append(_scenario("stale_source", "reject stale source before resume", stale_source, protected))

        def tampered_artifact() -> tuple[bool, None, dict[str, Any]]:
            run_dir, _, artifact = _session_fixture(root, "tampered_artifact")
            artifact.write_text('{"state":"tampered"}\n', encoding="utf-8")
            try:
                validate_checkpoint_for_resume(run_dir)
            except RuntimeError as exc:
                return True, None, {"error": clean_error(exc), "detection_point": "artifact_hash_preflight"}
            return False, None, {"detection_point": "missed"}

        scenarios.append(_scenario("tampered_artifact", "reject changed checkpoint evidence", tampered_artifact, protected))

        def cancelled_resume() -> tuple[bool, None, dict[str, Any]]:
            run_dir, _, _ = _session_fixture(root, "cancelled_resume")
            cancel_agent_session(run_dir, reason="failure-lab cancellation")
            try:
                validate_checkpoint_for_resume(run_dir)
            except ValueError as exc:
                return True, None, {"error": clean_error(exc), "detection_point": "authority_preflight"}
            return False, None, {"detection_point": "missed"}

        scenarios.append(_scenario("cancelled_resume", "cancelled sessions remain non-resumable", cancelled_resume, protected))

        def budget_recovery() -> tuple[bool, bool, dict[str, Any]]:
            run_dir = root / "budget_recovery"
            budget = ModelExecutionBudget(run_dir=run_dir, max_calls=1, max_runtime_seconds=60)
            call_id = budget.claim("planner", run_dir)
            budget.finish(call_id, "completed", {"schema": "fictionops.runner_receipt.v1", "usage": {"total_tokens": 100}})
            detected = False
            try:
                budget.claim("writer", run_dir)
            except ModelBudgetExceeded:
                detected = True
            resumed = start_model_budget(run_dir, max_calls=1, max_runtime_seconds=60, resume=True)
            resumed_id = resumed.claim("writer", run_dir)
            resumed.finish(resumed_id, "completed")
            return detected, resumed.used_calls == 1, {"detection_point": "pre_next_call", "cumulative_calls": resumed.payload()["cumulative_used_calls"]}

        scenarios.append(_scenario("budget_exhaustion", "stop before an over-budget call and resume in a new segment", budget_recovery, protected))

        def malformed_receipt() -> tuple[bool, None, dict[str, Any]]:
            try:
                parse_runner_receipt('FICTIONOPS_RUNNER_RECEIPT:{not-json}\n')
            except ValueError as exc:
                return True, None, {"error": clean_error(exc), "detection_point": "runner_receipt_parse"}
            return False, None, {"detection_point": "missed"}

        scenarios.append(_scenario("malformed_runner_receipt", "reject invalid telemetry without treating it as evidence", malformed_receipt, protected))

        def ungrounded_reviewer() -> tuple[bool, None, dict[str, Any]]:
            review = {"issues": [{"category": "character", "evidence": ["a sentence absent from the candidate"], "problem": "invented evidence"}]}
            issues = review_evidence_grounding_issues(review, "The candidate contains only visible action.")
            return bool(issues), None, {"detection_point": "review_grounding_gate", "issues": issues}

        scenarios.append(_scenario("ungrounded_reviewer", "reject reviewer findings absent from the candidate", ungrounded_reviewer, protected))

        def forbidden_story_state() -> tuple[bool, None, dict[str, Any]]:
            audit = deterministic_story_audit(
                "The envoy is guilty. The chapter closes this question as fact.",
                {"constraints": [{"id": "C1", "kind": "forbidden_conclusion", "text": "The envoy is guilty"}]},
            )
            return audit["status"] == "fail", None, {"detection_point": "deterministic_story_gate", "blocking_failures": audit["blocking_failures"]}

        scenarios.append(_scenario("forbidden_story_state", "block a forbidden conclusion before approval", forbidden_story_state, protected))

        detected = sum(bool(item["detected"]) for item in scenarios)
        protected_ok = sum(bool(item["protected_hash_unchanged"]) for item in scenarios)
        recoverable = [item for item in scenarios if item["recovery_succeeded"] is not None]
        return {
            "schema": FAILURE_LAB_SCHEMA,
            "scenario_count": len(scenarios),
            "detected_count": detected,
            "detection_rate": detected / len(scenarios),
            "protected_hash_success_rate": protected_ok / len(scenarios),
            "recoverable_count": len(recoverable),
            "recovery_success_rate": sum(bool(item["recovery_succeeded"]) for item in recoverable) / len(recoverable) if recoverable else 0.0,
            "scenarios": scenarios,
        }


def render_failure_lab(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported failure-lab format: {output_format}")
    lines = [
        "# FictionOps Agent Failure Lab",
        "",
        f"- Detection: {payload['detected_count']}/{payload['scenario_count']}",
        f"- Protected hash success: {payload['protected_hash_success_rate']:.3f}",
        f"- Recoverable success: {payload['recovery_success_rate']:.3f}",
        "",
        "| Scenario | Detected | Recovery | Protected | Detection point |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in payload["scenarios"]:
        lines.append(
            f"| `{item['scenario_id']}` | {'yes' if item['detected'] else 'no'} | "
            f"{item['recovery_succeeded'] if item['recovery_succeeded'] is not None else '-'} | "
            f"{'yes' if item['protected_hash_unchanged'] else 'no'} | `{item['details'].get('detection_point')}` |"
        )
    return "\n".join(lines).rstrip() + "\n"
