from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .agent_trajectory import append_trajectory


CHECKPOINT_SCHEMA = "fictionops.agent_checkpoint.v1"
CANCELLATION_SCHEMA = "fictionops.agent_cancellation.v1"
CHECKPOINT_PHASES = {
    "context_ready",
    "causal_ready",
    "plan_ready",
    "review_ready",
    "draft_ready",
    "candidate_ready",
    "verification_ready",
    "ready_for_approval",
    "needs_revision_attention",
    "applied",
    "cancelled",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text_file(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def checkpoint_files(run_dir: Path) -> dict[str, Path]:
    return {
        "session": run_dir / "session.json",
        "checkpoint": run_dir / "checkpoint.json",
        "cancellation": run_dir / "cancellation.json",
        "events": run_dir / "events.jsonl",
    }


def _load_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _artifact_records(paths: list[Path]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in paths:
        records.append(
            {
                "path": str(path.resolve()),
                "exists": path.is_file(),
                "size": path.stat().st_size if path.is_file() else 0,
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        )
    return records


def append_control_event(run_dir: Path, event: str, state: str, **details: object) -> None:
    path = checkpoint_files(run_dir)["events"]
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": "fictionops.revision_event.v1",
        "event": event,
        "state": state,
        "at": utc_now(),
        "details": details,
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    authority = "author" if event in {"session_cancelled", "candidate_accepted"} else "controller"
    append_trajectory(
        run_dir,
        kind="control_event",
        phase=state,
        actor="controller",
        observation={"event": event},
        action={key: value for key, value in details.items() if key in {"phase", "next_action", "reason", "resumed_from_phase", "final_phase"}},
        evidence=[{"name": key, "value": value} for key, value in details.items() if key not in {"phase", "next_action", "reason", "resumed_from_phase", "final_phase"}],
        authority=authority,
    )


def write_agent_checkpoint(
    run_dir: Path,
    *,
    phase: str,
    next_action: str,
    artifacts: list[Path] | None = None,
    resumable: bool = True,
    status: str = "completed",
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    if phase not in CHECKPOINT_PHASES:
        raise ValueError(f"unsupported checkpoint phase: {phase}")
    files = checkpoint_files(run_dir)
    if not files["session"].is_file():
        raise FileNotFoundError(f"checkpoint requires session.json: {run_dir}")
    session = _load_object(files["session"])
    now = utc_now()
    payload = {
        "schema": CHECKPOINT_SCHEMA,
        "session_id": session.get("session_id") or run_dir.name,
        "workflow": session.get("workflow"),
        "phase": phase,
        "status": status,
        "resumable": bool(resumable),
        "next_action": next_action,
        "source_file": session.get("source_file"),
        "source_sha256": session.get("source_sha256"),
        "engine_file": session.get("engine_file"),
        "engine_sha256": session.get("engine_sha256"),
        "artifacts": _artifact_records(artifacts or []),
        "details": details or {},
        "updated_at": now,
    }
    files["checkpoint"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    session.update(
        {
            "checkpoint_phase": phase,
            "checkpoint_file": str(files["checkpoint"].resolve()),
            "resumable": bool(resumable),
            "updated_at": now,
        }
    )
    files["session"].write_text(json.dumps(session, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    append_control_event(run_dir, "checkpoint_written", str(session.get("state") or phase), phase=phase, next_action=next_action)
    return payload


def load_agent_checkpoint(run_dir: Path) -> dict[str, object]:
    path = checkpoint_files(run_dir.expanduser().resolve())["checkpoint"]
    if not path.is_file():
        raise FileNotFoundError(f"agent checkpoint does not exist: {path}")
    payload = _load_object(path)
    if payload.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError(f"invalid agent checkpoint schema: {path}")
    return payload


def validate_checkpoint_for_resume(run_dir: Path) -> tuple[dict[str, object], dict[str, object]]:
    target = run_dir.expanduser().resolve()
    files = checkpoint_files(target)
    session = _load_object(files["session"])
    checkpoint = load_agent_checkpoint(target)
    if str(session.get("state")) == "cancelled" or not bool(checkpoint.get("resumable")):
        raise ValueError("agent checkpoint is not resumable")
    source_value = str(session.get("source_file") or checkpoint.get("source_file") or "")
    source_file = Path(source_value).expanduser().resolve() if source_value else None
    source_existed = bool(session.get("source_existed", True))
    expected_source = str(session.get("source_sha256") or checkpoint.get("source_sha256") or "")
    if source_file:
        if source_existed:
            if not source_file.is_file() or sha256_text_file(source_file) != expected_source:
                raise RuntimeError("source file changed after checkpoint; resume refused")
        elif source_file.exists():
            raise RuntimeError("previously absent target file now exists; resume refused")
    engine_value = str(session.get("engine_file") or checkpoint.get("engine_file") or "")
    expected_engine = str(session.get("engine_sha256") or checkpoint.get("engine_sha256") or "")
    if engine_value and expected_engine:
        engine_file = Path(engine_value).expanduser().resolve()
        if not engine_file.is_file() or sha256_text_file(engine_file) != expected_engine:
            raise RuntimeError("chapter engine changed after checkpoint; resume refused")
    for artifact in checkpoint.get("artifacts") or []:
        if not isinstance(artifact, dict) or not artifact.get("exists"):
            continue
        path = Path(str(artifact.get("path") or ""))
        expected = str(artifact.get("sha256") or "")
        if not path.is_file() or (expected and sha256_file(path) != expected):
            raise RuntimeError(f"checkpoint artifact changed; resume refused: {path}")
    return session, checkpoint


@dataclass
class AgentCancelReport:
    command: str
    run_dir: str
    session_id: str
    previous_state: str
    state: str
    reason: str
    cancellation_file: str
    checkpoint_file: str
    cancelled: bool


def cancel_agent_session(run_dir: Path, *, reason: str) -> AgentCancelReport:
    if not reason.strip():
        raise ValueError("agent cancel requires a reason")
    target = run_dir.expanduser().resolve()
    files = checkpoint_files(target)
    if not files["session"].is_file():
        raise FileNotFoundError(f"agent session does not exist: {files['session']}")
    session = _load_object(files["session"])
    previous = str(session.get("state") or "unknown")
    if previous == "applied":
        raise ValueError("an applied session cannot be cancelled")
    if previous == "cancelled" or files["cancellation"].exists():
        raise FileExistsError(files["cancellation"])
    now = utc_now()
    cancellation = {
        "schema": CANCELLATION_SCHEMA,
        "session_id": session.get("session_id") or target.name,
        "previous_state": previous,
        "state": "cancelled",
        "reason": reason.strip(),
        "cancelled_at": now,
    }
    files["cancellation"].write_text(json.dumps(cancellation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    session.update({"state": "cancelled", "ready_for_approval": False, "resumable": False, "cancelled_at": now, "updated_at": now})
    files["session"].write_text(json.dumps(session, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_agent_checkpoint(
        target,
        phase="cancelled",
        next_action="start_new_session_if_work_should_resume",
        artifacts=[files["cancellation"]],
        resumable=False,
        status="cancelled",
        details={"reason": reason.strip(), "previous_state": previous},
    )
    append_control_event(target, "session_cancelled", "cancelled", reason=reason.strip(), previous_state=previous)
    return AgentCancelReport(
        command="agent cancel",
        run_dir=str(target),
        session_id=str(session.get("session_id") or target.name),
        previous_state=previous,
        state="cancelled",
        reason=reason.strip(),
        cancellation_file=str(files["cancellation"]),
        checkpoint_file=str(files["checkpoint"]),
        cancelled=True,
    )


def render_agent_cancel(report: AgentCancelReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported agent cancel format: {output_format}")
    return (
        "# FictionOps Agent Cancel\n\n"
        f"- Session: `{report.session_id}`\n"
        f"- Previous state: `{report.previous_state}`\n"
        f"- State: `{report.state}`\n"
        f"- Reason: {report.reason}\n"
    )


@dataclass
class AgentResumeReport:
    command: str
    run_dir: str
    session_id: str
    workflow: str
    resumed_from_phase: str
    final_phase: str
    resumed: bool
    verification_status: str | None
    ready_for_approval: bool
    blocking_failures: list[str]
    model_calls_used: int
    cumulative_model_calls: int
    stop_reason: str
    checkpoint_file: str
    budget_file: str


def resume_agent_session(
    run_dir: Path,
    *,
    runner: list[str],
    timeout_seconds: int = 600,
    max_model_calls: int = 32,
    max_runtime_seconds: int = 3600,
    max_total_tokens: int | None = None,
    max_cost: float | None = None,
    cost_currency: str = "USD",
) -> AgentResumeReport:
    if not runner:
        raise ValueError("agent resume requires an explicit model runner")
    target = run_dir.expanduser().resolve()
    session, checkpoint = validate_checkpoint_for_resume(target)
    workflow = str(session.get("workflow") or "")
    phase = str(checkpoint.get("phase") or "")
    options = session.get("workflow_options") if isinstance(session.get("workflow_options"), dict) else {}
    chapter_file = Path(str(session.get("source_file") or ""))
    if workflow == "chapter_write":
        engine_file = Path(str(session.get("engine_file") or ""))
        outline_value = options.get("outline_file")
        outline_file = Path(str(outline_value)) if outline_value else None
        from .agent_write_workflow import build_agent_write_workflow

        report = build_agent_write_workflow(
            chapter_file,
            engine=engine_file,
            outline=outline_file,
            out_dir=str(target),
            provider=str(session.get("provider") or "") or None,
            model=str(session.get("model") or "") or None,
            runner=runner,
            timeout_seconds=timeout_seconds,
            max_model_calls=max_model_calls,
            max_runtime_seconds=max_runtime_seconds,
            max_total_tokens=max_total_tokens,
            max_cost=max_cost,
            cost_currency=cost_currency,
            min_chars=int(options.get("min_chars") or 200),
            max_retries=int(options.get("max_retries") or 1),
            max_context_files=int(options.get("max_context_files") or 24),
            max_context_chars=int(options.get("max_context_chars") or 100000),
            use_memory=bool(options.get("use_memory", True)),
            use_causal_simulation=bool(options.get("use_causal_simulation", True)),
            use_adversarial_review=bool(options.get("use_adversarial_review", True)),
            scene_by_scene=bool(options.get("scene_by_scene", False)),
            resume=True,
        )
    elif workflow == "chapter_revision":
        from .agent_revise_workflow import build_agent_revise_workflow

        bundled_review = target / "review_workflow.md"
        report = build_agent_revise_workflow(
            chapter_file,
            review=bundled_review if bundled_review.is_file() else None,
            out_dir=str(target),
            role=str(options.get("role") or "style-auditor"),
            provider=str(session.get("provider") or "") or None,
            model=str(session.get("model") or "") or None,
            runner=runner,
            output_name=str(options.get("output_name") or "output.md"),
            timeout_seconds=timeout_seconds,
            max_model_calls=max_model_calls,
            max_runtime_seconds=max_runtime_seconds,
            max_total_tokens=max_total_tokens,
            max_cost=max_cost,
            cost_currency=cost_currency,
            max_chapter_chars=int(options.get("max_chapter_chars") or 120000),
            max_review_chars=int(options.get("max_review_chars") or 50000),
            max_retries=int(options.get("max_retries") or 1),
            semantic_verify=bool(options.get("semantic_verify", True)),
            review_scope=str(options.get("review_scope") or "comprehensive"),
            max_context_files=int(options.get("max_context_files") or 24),
            max_project_context_chars=int(options.get("max_project_context_chars") or 100000),
            use_memory=bool(options.get("use_memory", True)),
            resume=True,
        )
    else:
        raise ValueError(f"agent resume does not support workflow yet: {workflow}")
    updated_session = _load_object(checkpoint_files(target)["session"])
    updated_session.update(
        {
            "resume_count": int(updated_session.get("resume_count") or 0) + 1,
            "last_resumed_from_phase": phase,
            "last_resumed_at": utc_now(),
        }
    )
    checkpoint_files(target)["session"].write_text(
        json.dumps(updated_session, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    final_checkpoint = load_agent_checkpoint(target)
    budget = _load_object(target / "model_budget.json")
    append_control_event(
        target,
        "session_resumed",
        str(updated_session.get("state") or final_checkpoint.get("phase")),
        resumed_from_phase=phase,
        final_phase=final_checkpoint.get("phase"),
        model_calls_used=budget.get("used_calls"),
    )
    return AgentResumeReport(
        command="agent resume",
        run_dir=str(target),
        session_id=str(updated_session.get("session_id") or target.name),
        workflow=workflow,
        resumed_from_phase=phase,
        final_phase=str(final_checkpoint.get("phase") or ""),
        resumed=True,
        verification_status=report.verification_status,
        ready_for_approval=report.ready_for_approval,
        blocking_failures=[str(item) for item in (report.verification or {}).get("blocking_failures") or []],
        model_calls_used=int(budget.get("used_calls") or 0),
        cumulative_model_calls=int(budget.get("cumulative_used_calls") or budget.get("used_calls") or 0),
        stop_reason=report.stop_reason,
        checkpoint_file=str(checkpoint_files(target)["checkpoint"]),
        budget_file=str(target / "model_budget.json"),
    )


def render_agent_resume(report: AgentResumeReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported agent resume format: {output_format}")
    return (
        "# FictionOps Agent Resume\n\n"
        f"- Session: `{report.session_id}`\n"
        f"- From: `{report.resumed_from_phase}`\n"
        f"- Final: `{report.final_phase}`\n"
        f"- Calls: {report.model_calls_used} (cumulative {report.cumulative_model_calls})\n"
        f"- Ready for approval: {'yes' if report.ready_for_approval else 'no'}\n"
        f"- Stop reason: `{report.stop_reason}`\n"
    )
