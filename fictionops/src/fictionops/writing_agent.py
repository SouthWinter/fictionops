from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .agent_exec import DEFAULT_AGENT_EXEC_OUTPUT, build_agent_exec
from .agent_inbox import build_agent_inbox
from .agent_run import build_agent_run
from .models import AgentInboxReport, AgentRunReport, WritingAgentCommandReport
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


COMMAND_DEFAULTS = {
    "write-chapter": {"role": "draft-writer", "task": "draft", "prefix": "write"},
    "revise-chapter": {"role": "style-auditor", "task": "review", "prefix": "revise"},
    "audit-chapter": {"role": "info-boundary-auditor", "task": "review", "prefix": "audit"},
}


def default_agent_command_out_dir(command: str, *, book: str, chapter: str | None) -> str:
    config = COMMAND_DEFAULTS[command]
    chapter_part = f"_ch_{chapter}" if chapter else ""
    return f"00_management/agent_runs/{config['prefix']}_{book}{chapter_part}"


def staged_outputs_from_inbox(inbox: AgentInboxReport) -> list[dict[str, object]]:
    outputs: list[dict[str, object]] = []
    for run in inbox.runs:
        if not run.output_file:
            continue
        outputs.append(
            {
                "run_dir": run.run_dir,
                "output_file": run.output_file,
                "role": run.role,
                "task": run.task,
                "book": run.book,
                "chapter": run.chapter,
                "state": "draft" if run.task == "draft" else "audit",
                "review_required": True,
                "output_chars": run.output_chars,
            }
        )
    return outputs


def next_actions_for_writing_agent(report: WritingAgentCommandReport) -> list[str]:
    if report.executed and report.ready_count > 0:
        return [
            f"Review staged output with `fictionops agent-inbox {report.run_dir}`.",
            "Apply accepted changes manually; do not treat model output as canon by default.",
        ]
    if report.executed:
        return [f"Inspect the run with `fictionops agent-inbox {report.run_dir}` before retrying or applying anything."]
    return [
        f"Run a model or external runner with `fictionops agent-exec {report.run_dir} --runner ...`.",
        f"Then inspect staged output with `fictionops agent-inbox {report.run_dir}`.",
    ]


def build_writing_agent_command(
    project: Path,
    *,
    command: str,
    book: str = "book_01",
    chapter: str | None = None,
    role: str | None = None,
    out_dir: str | None = None,
    runner: list[str] | None = None,
    output_name: str = DEFAULT_AGENT_EXEC_OUTPUT,
    timeout_seconds: int = 300,
    include_context_content: bool = True,
    max_chars_per_file: int = 6000,
    max_total_context_chars: int = 60000,
    force: bool = False,
    force_output: bool = False,
    dry_run: bool = False,
) -> WritingAgentCommandReport:
    if command not in COMMAND_DEFAULTS:
        raise ValueError(f"unknown writing agent command: {command}")
    config = COMMAND_DEFAULTS[command]
    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter) if chapter else None
    selected_role = role or str(config["role"])
    selected_task = str(config["task"])
    selected_out_dir = out_dir or default_agent_command_out_dir(command, book=book_id, chapter=chapter_number)

    agent_run = build_agent_run(
        project,
        role=selected_role,
        task=selected_task,
        book=book_id,
        chapter=chapter_number,
        out_dir=selected_out_dir,
        include_context_content=include_context_content,
        max_chars_per_file=max_chars_per_file,
        max_total_context_chars=max_total_context_chars,
        force=force,
        dry_run=dry_run,
    )

    agent_exec = None
    inbox = None
    executed = False
    staged_outputs: list[dict[str, object]] = []
    stop_reason = "agent_run_ready_for_runner"

    if runner:
        if dry_run:
            stop_reason = "dry_run_runner_not_executed"
        else:
            agent_exec = build_agent_exec(
                Path(agent_run.output_dir or selected_out_dir),
                command=runner,
                output_name=output_name,
                timeout_seconds=timeout_seconds,
                force=force_output or force,
                dry_run=False,
            )
            executed = True
            inbox = build_agent_inbox(Path(agent_run.output_dir or selected_out_dir), output_name=output_name)
            staged_outputs = staged_outputs_from_inbox(inbox)
            stop_reason = "staged_output_ready_for_review" if inbox.ready_count > 0 else "agent_output_needs_attention"

    report = WritingAgentCommandReport(
        command=command,
        target=str(project.expanduser().resolve()),
        role=agent_run.role,
        task=agent_run.task,
        book=book_id,
        chapter=chapter_number,
        run_dir=agent_run.output_dir,
        prepared=agent_run.written,
        executed=executed,
        inbox_status=inbox.status if inbox else None,
        ready_count=inbox.ready_count if inbox else 0,
        staged_outputs=staged_outputs,
        stop_reason=stop_reason,
        next_actions=[],
        agent_run=agent_run,
        agent_exec=agent_exec,
        inbox=inbox,
    )
    report.next_actions = next_actions_for_writing_agent(report)
    return report


def render_writing_agent_command(report: WritingAgentCommandReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_writing_agent_command(report)


def format_writing_agent_command(report: WritingAgentCommandReport) -> str:
    lines = [
        f"# FictionOps {report.command}",
        "",
        f"- Target: `{report.target}`",
        f"- Role: `{report.role}`",
        f"- Task: `{report.task}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Run dir: `{report.run_dir or '-'}`",
        f"- Prepared: {'yes' if report.prepared else 'no'}",
        f"- Executed runner: {'yes' if report.executed else 'no'}",
        f"- Inbox status: `{report.inbox_status or '-'}`",
        f"- Ready staged outputs: {report.ready_count}",
        f"- Stop reason: `{report.stop_reason}`",
        "",
        "## Staged Outputs",
        "",
    ]
    if report.staged_outputs:
        lines.extend(["| State | Role | Task | Output |", "| --- | --- | --- | --- |"])
        for item in report.staged_outputs:
            lines.append(f"| `{item['state']}` | `{item['role']}` | `{item['task']}` | `{item['output_file']}` |")
    else:
        lines.append("No staged output is ready yet.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
