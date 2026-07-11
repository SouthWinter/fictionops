from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .agent_issue_ledger import reconcile_run_issue_states
from .agent_memory import discover_memory_root, memory_paths, record_acceptance_memory
from .agent_session_control import write_agent_checkpoint
from .agent_revision_runtime import append_event, revision_runtime_files, sha256_file, sha256_text, utc_now, write_json


@dataclass
class AgentRevisionAcceptReport:
    command: str
    run_dir: str
    session_id: str
    source_file: str
    candidate_file: str
    source_sha256_expected: str
    source_sha256_actual: str
    candidate_sha256_expected: str
    candidate_sha256_actual: str
    verification_status: str
    dry_run: bool
    applied: bool
    learning_recorded: bool
    memory_event_file: str
    acceptance_file: str
    stop_reason: str
    next_actions: list[str]


def load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def atomic_apply_text(source_file: Path, text: str, session_id: str) -> None:
    source_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = source_file.with_name(f".{source_file.name}.{session_id}.tmp")
    try:
        temporary.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
        os.replace(temporary, source_file)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_agent_revision_accept(run_dir: Path, *, dry_run: bool = False) -> AgentRevisionAcceptReport:
    if not run_dir.exists():
        raise FileNotFoundError(f"revision run directory does not exist: {run_dir}")
    if not run_dir.is_dir():
        raise ValueError(f"agent-accept-revision requires a revision run directory: {run_dir}")
    target = run_dir.expanduser().resolve()
    files = revision_runtime_files(target)
    session = load_json_object(files["session"])
    verification = load_json_object(files["verification"])
    if verification.get("status") != "ready_for_approval" or not verification.get("ready_for_approval"):
        raise ValueError("revision candidate has not passed verification and cannot be accepted.")
    source_file = Path(str(session.get("source_file") or verification.get("source_file") or "")).expanduser().resolve()
    candidate_file = Path(str(session.get("candidate_file") or verification.get("candidate_file") or "")).expanduser().resolve()
    source_existed = bool(session.get("source_existed", True))
    if source_existed and not source_file.is_file():
        raise FileNotFoundError(f"source chapter does not exist: {source_file}")
    if not source_existed and source_file.exists():
        raise RuntimeError("target chapter was created after the writing session started; acceptance was refused to protect the newer file.")
    if not candidate_file.is_file():
        raise FileNotFoundError(f"candidate chapter does not exist: {candidate_file}")
    expected_source = str(session.get("source_sha256") or verification.get("source_sha256") or "")
    expected_candidate = str(session.get("candidate_sha256") or verification.get("candidate_sha256") or "")
    actual_source = sha256_file(source_file) if source_existed else sha256_text("")
    actual_candidate = sha256_file(candidate_file)
    if actual_source != expected_source:
        raise RuntimeError("source chapter changed after the revision session started; acceptance was refused to protect newer edits.")
    if actual_candidate != expected_candidate:
        raise RuntimeError("candidate chapter changed after verification; rerun verification before accepting it.")
    acceptance_file = target / "acceptance.json"
    if acceptance_file.exists():
        raise FileExistsError(acceptance_file)
    session_id = str(session.get("session_id") or target.name)
    applied = False
    learning_recorded = False
    memory_event_file = str(memory_paths(discover_memory_root(source_file))["acceptances"])
    stop_reason = "acceptance_preflight_passed"
    if not dry_run:
        candidate_text = candidate_file.read_text(encoding="utf-8")
        atomic_apply_text(source_file, candidate_text, session_id)
        applied_hash = sha256_file(source_file)
        if applied_hash != expected_candidate:
            raise RuntimeError("source chapter hash did not match the accepted candidate after atomic apply.")
        accepted_at = utc_now()
        acceptance = {
            "schema": "fictionops.revision_acceptance.v1",
            "session_id": session_id,
            "source_file": str(source_file),
            "source_sha256_before": actual_source,
            "source_sha256_after": applied_hash,
            "candidate_file": str(candidate_file),
            "candidate_sha256": actual_candidate,
            "accepted_at": accepted_at,
            "applied": True,
        }
        write_json(acceptance_file, acceptance)
        session.update(
            {
                "state": "applied",
                "ready_for_approval": False,
                "source_sha256_after": applied_hash,
                "accepted_at": accepted_at,
                "updated_at": accepted_at,
            }
        )
        write_json(files["session"], session, force=True)
        reconcile_run_issue_states(target, accepted=True)
        append_event(target, "candidate_accepted", "applied", source_file=str(source_file), source_sha256_after=applied_hash)
        write_agent_checkpoint(
            target,
            phase="applied",
            next_action="review_retrospective_and_canon_sync",
            artifacts=[source_file, acceptance_file],
            resumable=False,
            status="completed",
        )
        suggestions: list[object] = []
        canon_file = target / "canon_sync_suggestions.json"
        if canon_file.exists():
            raw_canon = load_json_object(canon_file)
            if isinstance(raw_canon.get("suggestions"), list):
                suggestions = list(raw_canon["suggestions"])
        record_acceptance_memory(
            source_file,
            session_id=session_id,
            source_file=source_file,
            source_sha256_before=actual_source,
            source_sha256_after=applied_hash,
            run_dir=target,
            canon_sync_suggestions=suggestions,
        )
        learning_recorded = True
        applied = True
        stop_reason = "revision_applied"
    report = AgentRevisionAcceptReport(
        command="agent-accept-revision",
        run_dir=str(target),
        session_id=session_id,
        source_file=str(source_file),
        candidate_file=str(candidate_file),
        source_sha256_expected=expected_source,
        source_sha256_actual=actual_source,
        candidate_sha256_expected=expected_candidate,
        candidate_sha256_actual=actual_candidate,
        verification_status=str(verification.get("status")),
        dry_run=dry_run,
        applied=applied,
        learning_recorded=learning_recorded,
        memory_event_file=memory_event_file,
        acceptance_file=str(acceptance_file),
        stop_reason=stop_reason,
        next_actions=(
            ["Rerun without `--dry-run` to atomically apply the verified candidate."]
            if dry_run
            else (
                [
                    "Review the applied chapter and the session's `retrospective.draft.md`.",
                    "Apply accepted `canon_sync_suggestions.json` items to project memory, then close the chapter session.",
                ]
                if session.get("workflow") == "chapter_write"
                else ["Review the applied chapter, then update its retrospective or canon-sync notes before closing the session."]
            )
        ),
    )
    return report


def render_agent_revision_accept(report: AgentRevisionAcceptReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported agent-accept-revision format: {output_format}")
    lines = [
        "# FictionOps Agent Revision Acceptance",
        "",
        f"- Session: `{report.session_id}`",
        f"- Source: `{report.source_file}`",
        f"- Candidate: `{report.candidate_file}`",
        f"- Verification: `{report.verification_status}`",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        f"- Applied: {'yes' if report.applied else 'no'}",
        f"- Acceptance memory recorded: {'yes' if report.learning_recorded else 'no'}",
        f"- Stop reason: `{report.stop_reason}`",
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in report.next_actions)
    return "\n".join(lines).rstrip() + "\n"
