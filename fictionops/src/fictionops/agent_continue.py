from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .agent_memory import build_memory_index, memory_status
from .agent_issue_ledger import issue_ledger_path, load_issue_ledger
from .agent_policy import select_agent_policy
from .agent_project_context import discover_project_root


AGENT_CONTINUE_SCHEMA = "fictionops.agent_continue.v1"
@dataclass
class AgentContinueReport:
    command: str
    schema: str
    project_root: str
    observed_session_count: int
    latest_session: dict[str, object] | None
    memory: dict[str, object]
    counterevidence: dict[str, object]
    selected_action: str
    reason: str
    risk: str
    requires_human: bool
    executable: bool
    executed: bool
    stop_reason: str
    suggested_command: str | None
    evidence_files: list[str]
    result: dict[str, object] | None


def _management_dirs(root: Path) -> list[Path]:
    return [path for name in ("00_management", "00_总纲与管理") if (path := root / name).is_dir()]


def discover_agent_sessions(root: Path) -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    seen: set[Path] = set()
    for management in _management_dirs(root):
        for pattern in ("agent_runs/**/session.json", "agent_sessions/**/session.json"):
            for path in management.glob(pattern):
                resolved = path.resolve()
                if resolved in seen or not path.is_file():
                    continue
                seen.add(resolved)
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    payload = {"state": "invalid_session", "session_id": path.parent.name}
                if not isinstance(payload, dict):
                    payload = {"state": "invalid_session", "session_id": path.parent.name}
                budget_file = path.parent / "model_budget.json"
                checkpoint_file = path.parent / "checkpoint.json"
                budget: dict[str, object] | None = None
                checkpoint: dict[str, object] | None = None
                if budget_file.exists():
                    try:
                        parsed = json.loads(budget_file.read_text(encoding="utf-8"))
                        budget = parsed if isinstance(parsed, dict) else None
                    except (OSError, json.JSONDecodeError):
                        budget = {"status": "invalid"}
                if checkpoint_file.exists():
                    try:
                        parsed = json.loads(checkpoint_file.read_text(encoding="utf-8"))
                        checkpoint = parsed if isinstance(parsed, dict) else None
                    except (OSError, json.JSONDecodeError):
                        checkpoint = {"status": "invalid"}
                sessions.append(
                    {
                        "session_id": payload.get("session_id") or path.parent.name,
                        "state": payload.get("state") or "unknown",
                        "ready_for_approval": bool(payload.get("ready_for_approval")),
                        "source_file": payload.get("source_file") or payload.get("target_file"),
                        "run_dir": str(path.parent.resolve()),
                        "session_file": str(resolved),
                        "updated_at": payload.get("updated_at") or payload.get("created_at"),
                        "mtime_ns": path.stat().st_mtime_ns,
                        "budget": budget,
                        "checkpoint": checkpoint,
                    }
                )
    sessions.sort(key=lambda item: int(item.get("mtime_ns") or 0), reverse=True)
    return sessions


def _canon_sync_pending(run_dir: Path) -> bool:
    path = run_dir / "canon_sync_suggestions.json"
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    return bool(payload.get("suggestions")) if isinstance(payload, dict) else True


def build_agent_continue(path: Path, *, execute: bool = False) -> AgentContinueReport:
    root = discover_project_root(path.expanduser().resolve())
    sessions = discover_agent_sessions(root)
    latest = sessions[0] if sessions else None
    memory = memory_status(root)
    issue_payload = load_issue_ledger(root)
    persistent_issues = [item for item in issue_payload.get("issues") or [] if isinstance(item, dict)]
    counterevidence_issues = [item for item in persistent_issues if isinstance(item.get("counterevidence"), dict)]
    counterevidence = {
        "issue_count": len(counterevidence_issues),
        "open_count": sum(str(item.get("status")) == "open" for item in counterevidence_issues),
        "evidence_blocked_count": sum(str(item.get("status")) == "evidence_blocked" for item in counterevidence_issues),
        "model_withdrawn_count": sum(str(item.get("status")) == "model_withdrawn" for item in counterevidence_issues),
        "open_issue_ids": [str(item.get("issue_id")) for item in counterevidence_issues if str(item.get("status")) == "open"],
        "evidence_blocked_issue_ids": [str(item.get("issue_id")) for item in counterevidence_issues if str(item.get("status")) == "evidence_blocked"],
        "model_withdrawn_issue_ids": [str(item.get("issue_id")) for item in counterevidence_issues if str(item.get("status")) == "model_withdrawn"],
    }
    action = "inspect_project"
    reason = "No safe automatic transition is currently justified."
    risk = "R0"
    requires_human = False
    executable = False
    suggested_command: str | None = None
    evidence: list[str] = []
    latest_queue_file: Path | None = None
    counterevidence_bundle_dir: Path | None = None
    counterevidence_candidate_state: str | None = None
    if counterevidence_issues:
        evidence.append(str(issue_ledger_path(root).resolve()))
        application_files = sorted(root.rglob("counterevidence_application.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True)
        queue_files = sorted(root.rglob("counterevidence_reviser_queue.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True)
        open_ids = set(counterevidence["open_issue_ids"])
        for queue_file in queue_files:
            try:
                queue_payload = json.loads(queue_file.read_text(encoding="utf-8-sig"))
                queue_ids = {str(item) for item in queue_payload.get("issue_ids") or []} if isinstance(queue_payload, dict) else set()
            except (OSError, json.JSONDecodeError):
                continue
            if queue_ids and queue_ids.issubset(open_ids):
                latest_queue_file = queue_file.resolve()
                source_application = Path(str(queue_payload.get("source_application") or "")).expanduser().resolve()
                if source_application.is_file():
                    evidence.append(str(source_application))
                break
        if latest_queue_file is not None:
            evidence.append(str(latest_queue_file))
            counterevidence_bundle_dir = latest_queue_file.parent / "counterevidence_revision_bundle"
            candidate_file = counterevidence_bundle_dir / "output.md"
            verification_file = counterevidence_bundle_dir / "counterevidence_verification.json"
            if candidate_file.is_file():
                evidence.append(str(candidate_file.resolve()))
                counterevidence_candidate_state = "awaiting_verification"
                if verification_file.is_file():
                    evidence.append(str(verification_file.resolve()))
                    try:
                        verification = json.loads(verification_file.read_text(encoding="utf-8-sig"))
                        counterevidence_candidate_state = (
                            "ready_for_approval" if isinstance(verification, dict) and verification.get("ready_for_approval") else "needs_revision_attention"
                        )
                    except (OSError, json.JSONDecodeError):
                        counterevidence_candidate_state = "needs_revision_attention"
        elif application_files:
            evidence.append(str(application_files[0].resolve()))

    state = None
    ready_for_approval = False
    budget_status = None
    canon_sync_pending = False
    run_dir: Path | None = None
    if latest:
        run_dir = Path(str(latest["run_dir"]))
        state = str(latest.get("state") or "unknown")
        budget = latest.get("budget") if isinstance(latest.get("budget"), dict) else {}
        ready_for_approval = bool(latest.get("ready_for_approval"))
        budget_status = str(budget.get("status") or "") or None
        canon_sync_pending = state == "applied" and _canon_sync_pending(run_dir)
        evidence.append(str(latest["session_file"]))
        if budget:
            evidence.append(str((run_dir / "model_budget.json").resolve()))
        if canon_sync_pending:
            evidence.append(str((run_dir / "canon_sync_suggestions.json").resolve()))

    policy = select_agent_policy(
        state=state,
        ready_for_approval=ready_for_approval,
        budget_status=budget_status,
        memory_stale=bool(memory.get("stale")),
        canon_sync_pending=canon_sync_pending,
        counterevidence_open_count=int(counterevidence["open_count"]),
        counterevidence_blocked_count=int(counterevidence["evidence_blocked_count"]),
        counterevidence_withdrawn_count=int(counterevidence["model_withdrawn_count"]),
        counterevidence_candidate_state=counterevidence_candidate_state,
    )
    action = policy.action
    reason = policy.reason
    risk = policy.risk
    requires_human = policy.authority == "author"
    executable = policy.executable
    if action == "review_candidate" and run_dir is not None:
        suggested_command = f'fictionops agent accept "{run_dir}" --dry-run'
    elif action == "inspect_failed_candidate":
        suggested_command = f'fictionops agent continue "{root}"'
    elif action == "rebuild_memory":
        suggested_command = f'fictionops agent-memory build "{root}"'
        evidence.append(str(memory.get("index_file") or ""))
    elif action == "prepare_counterevidence_revision":
        if latest_queue_file is not None:
            suggested_command = f'fictionops agent counterevidence prepare-revision "{latest_queue_file.parent}"'
        else:
            suggested_command = f'fictionops agent issues "{root}" --status open --format json'
    elif action == "verify_counterevidence_revision" and counterevidence_bundle_dir is not None:
        suggested_command = f'fictionops agent counterevidence verify-revision "{counterevidence_bundle_dir}" --runner ...'
    elif action == "revise_counterevidence_candidate" and counterevidence_bundle_dir is not None:
        suggested_command = f'fictionops agent-exec "{counterevidence_bundle_dir}" --force --runner ...'
    elif action == "review_counterevidence_candidate" and counterevidence_bundle_dir is not None:
        suggested_command = f'fictionops agent counterevidence accept-revision "{counterevidence_bundle_dir}" --dry-run'
    elif action == "retrieve_counterevidence":
        suggested_command = f'fictionops agent issues "{root}" --status evidence_blocked --format json'
    elif action == "review_model_withdrawals":
        suggested_command = f'fictionops agent issues "{root}" --status model_withdrawn --format json'

    executed = False
    result: dict[str, object] | None = None
    stop_reason = "action_ready"
    if execute:
        if action == "rebuild_memory":
            result = build_memory_index(root, write=True)
            memory = memory_status(root)
            executed = True
            stop_reason = "safe_action_completed"
        elif requires_human:
            stop_reason = "human_authority_required"
        else:
            stop_reason = "no_safe_automatic_action"

    latest_public = None
    if latest:
        latest_public = {key: value for key, value in latest.items() if key != "mtime_ns"}
    return AgentContinueReport(
        command="agent continue",
        schema=AGENT_CONTINUE_SCHEMA,
        project_root=str(root),
        observed_session_count=len(sessions),
        latest_session=latest_public,
        memory=memory,
        counterevidence=counterevidence,
        selected_action=action,
        reason=reason,
        risk=risk,
        requires_human=requires_human,
        executable=executable,
        executed=executed,
        stop_reason=stop_reason,
        suggested_command=suggested_command,
        evidence_files=[item for item in evidence if item],
        result=result,
    )


def render_agent_continue(report: AgentContinueReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported agent continue format: {output_format}")
    lines = [
        "# FictionOps Agent Continue",
        "",
        f"- Project: `{report.project_root}`",
        f"- Observed sessions: {report.observed_session_count}",
        f"- Selected action: `{report.selected_action}`",
        f"- Risk: `{report.risk}`",
        f"- Requires human: {'yes' if report.requires_human else 'no'}",
        f"- Executed: {'yes' if report.executed else 'no'}",
        f"- Stop reason: `{report.stop_reason}`",
        f"- Counterevidence: open {report.counterevidence['open_count']}, blocked {report.counterevidence['evidence_blocked_count']}, model-withdrawn {report.counterevidence['model_withdrawn_count']}",
        "",
        report.reason,
    ]
    if report.suggested_command:
        lines.extend(["", f"Next command: `{report.suggested_command}`"])
    return "\n".join(lines).rstrip() + "\n"
