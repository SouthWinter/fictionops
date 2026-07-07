from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from .agent_connect import normalize_connector_name
from .agent_exec import DEFAULT_AGENT_EXEC_OUTPUT, build_agent_exec
from .agent_inbox import build_agent_inbox
from .agent_run import build_agent_run
from .agent_workflow_audit import build_agent_workflow_audit, connector_dir_for, normalize_agent_workflow_level
from .models import AgentSmokeReport, AgentSmokeStep
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


DEFAULT_AGENT_SMOKE_CHAPTER = "001"


def connector_manifest_mode(project: Path, connector_name: str) -> str | None:
    manifest_file = connector_dir_for(project, connector_name) / "connector_manifest.json"
    if not manifest_file.exists():
        return None
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    mode = str(data.get("mode") or "").strip()
    return mode or None


def default_agent_smoke_run_dir(connector_name: str, chapter: str) -> str:
    return f"00_management/agent_runs/{connector_name}_smoke_ch_{chapter}"


def next_actions_for_agent_smoke(report: AgentSmokeReport) -> list[str]:
    if report.status == "not_ready":
        return ["Fix the connector or project audit findings, then rerun `fictionops agent-smoke`."]
    if report.dry_run:
        return ["Rerun without `--dry-run` to create the smoke task bundle and staged output."]
    if report.status == "smoke_passed":
        return [
            f"Review the staged smoke output in `{report.run_dir}`.",
            "Replace the stub adapter only after the smoke boundary is understood.",
            f"Rerun `fictionops audit-agent-workflow {report.target} --level {report.level} --connector {report.connector_name}` before trusting a real runner.",
        ]
    return ["Inspect the smoke report, fix the failed step, then rerun with a fresh `--out-dir` or `--force`."]


def step(name: str, status: str, summary: str) -> AgentSmokeStep:
    return AgentSmokeStep(name=name, status=status, summary=summary)


def audit_blocked_only_by_current_smoke_run(project: Path, run_dir: Path, issue_codes: set[str]) -> bool:
    allowed_codes = {"agent_output_waiting_for_review", "agent_inbox_needs_attention"}
    if not issue_codes or not issue_codes.issubset(allowed_codes):
        return False
    inbox = build_agent_inbox(project)
    active_runs = [item for item in inbox.runs if item.state != "awaiting_output"]
    if not active_runs:
        return False
    current = run_dir.resolve()
    return all(Path(item.run_dir).resolve() == current for item in active_runs)


def build_agent_smoke(
    project: Path,
    *,
    connector: str,
    level: str | None = None,
    role: str = "draft-writer",
    book: str = "book_01",
    chapter: str = DEFAULT_AGENT_SMOKE_CHAPTER,
    out_dir: str | None = None,
    output_name: str = DEFAULT_AGENT_EXEC_OUTPUT,
    timeout_seconds: int = 60,
    force: bool = False,
    dry_run: bool = False,
) -> AgentSmokeReport:
    if timeout_seconds <= 0:
        raise ValueError("agent-smoke --timeout-seconds must be greater than zero.")
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"agent-smoke requires a FictionOps project directory: {project}")

    target = project.expanduser().resolve()
    connector_name = normalize_connector_name(connector)
    manifest_level = connector_manifest_mode(target, connector_name)
    audit_level = normalize_agent_workflow_level(level or manifest_level or "runner")
    book_id = normalize_book_for_plan(book)
    chapter_id = normalize_chapter_number(chapter)
    run_dir_text = out_dir or default_agent_smoke_run_dir(connector_name, chapter_id)
    run_dir = (target / run_dir_text).resolve() if not Path(run_dir_text).expanduser().is_absolute() else Path(run_dir_text).expanduser().resolve()
    adapter_file = connector_dir_for(target, connector_name) / "runner_adapter.py"

    steps: list[AgentSmokeStep] = []
    audit = build_agent_workflow_audit(target, level=audit_level, book=book_id, chapter=chapter_id, connector=connector_name)
    steps.append(step("audit-agent-workflow", "passed" if audit.ready else "failed", f"{audit.status}; blocking issues: {audit.blocking_issue_count}"))
    audit_can_proceed = audit.ready
    if not audit_can_proceed and force:
        issue_codes = {item.code for item in audit.issues if item.severity in {"P0", "P1", "P2"}}
        if audit_blocked_only_by_current_smoke_run(target, run_dir, issue_codes):
            audit_can_proceed = True
            steps.append(step("force-current-smoke-run", "overridden", "Only the current smoke run has staged output; --force will overwrite it."))

    agent_run = None
    agent_exec = None
    inbox = None
    status = "not_ready"
    ready = False
    written = False

    if audit_can_proceed:
        if dry_run:
            steps.append(step("agent-run", "planned", str(run_dir)))
            steps.append(step("agent-exec", "planned", str(adapter_file)))
            steps.append(step("agent-inbox", "planned", str(run_dir)))
            status = "dry_run"
            ready = True
        else:
            agent_run = build_agent_run(
                target,
                role=role,
                book=book_id,
                chapter=chapter_id,
                out_dir=str(run_dir),
                include_context_content=False,
                force=force,
            )
            steps.append(step("agent-run", "passed" if agent_run.written else "failed", f"bundle files: {agent_run.file_count}"))

            agent_exec = build_agent_exec(
                run_dir,
                command=[sys.executable, str(adapter_file)],
                output_name=output_name,
                timeout_seconds=timeout_seconds,
                force=force,
            )
            steps.append(step("agent-exec", "passed" if agent_exec.written else "failed", f"stdout chars: {agent_exec.stdout_chars}"))

            inbox = build_agent_inbox(run_dir, output_name=output_name)
            inbox_ok = inbox.status == "ready_for_review" and inbox.ready_count == 1 and inbox.needs_attention_count == 0
            steps.append(step("agent-inbox", "passed" if inbox_ok else "failed", f"{inbox.status}; ready: {inbox.ready_count}"))
            status = "smoke_passed" if inbox_ok else "smoke_failed"
            ready = inbox_ok
            written = bool(agent_run.written and agent_exec.written)

    report = AgentSmokeReport(
        target=str(target),
        connector_name=connector_name,
        level=audit_level,
        status=status,
        ready=ready,
        run_dir=str(run_dir),
        adapter_file=str(adapter_file),
        output_name=output_name,
        dry_run=dry_run,
        written=written,
        step_count=len(steps),
        steps=steps,
        audit=audit,
        agent_run=agent_run,
        agent_exec=agent_exec,
        inbox=inbox,
        next_actions=[],
    )
    report.next_actions = next_actions_for_agent_smoke(report)
    return report


def format_agent_smoke(report: AgentSmokeReport) -> str:
    lines = [
        "# FictionOps Agent Smoke",
        "",
        f"- Target: `{report.target}`",
        f"- Connector: `{report.connector_name}`",
        f"- Level: `{report.level}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Run dir: `{report.run_dir}`",
        f"- Adapter: `{report.adapter_file}`",
        f"- Output name: `{report.output_name}`",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        f"- Written: {'yes' if report.written else 'no'}",
        "",
        "## Steps",
        "",
        "| Step | Status | Summary |",
        "| --- | --- | --- |",
    ]
    for item in report.steps:
        lines.append(f"| `{item.name}` | `{item.status}` | {item.summary} |")
    lines.extend(["", "## Rule", ""])
    lines.append("This smoke test proves the connector staging boundary. It does not prove model quality and does not apply staged output to manuscript or canon files.")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_agent_smoke(report: AgentSmokeReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_smoke(report)
