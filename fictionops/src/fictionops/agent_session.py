from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .agent_inbox import build_agent_inbox
from .models import AgentSessionFile, AgentSessionReport, AgentSessionStep
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


SESSION_STAGE_DEFAULTS = {
    "write": {"command": "write-chapter", "role": "draft-writer", "task": "draft"},
    "revise": {"command": "revise-chapter", "role": "style-auditor", "task": "review"},
    "audit": {"command": "audit-chapter", "role": "info-boundary-auditor", "task": "review"},
}
DEFAULT_SESSION_STAGES = ["write", "revise", "audit"]


def slugify_session_id(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", text.strip()).strip("-_.")
    return cleaned.lower() or "session"


def normalize_session_stages(stages: str | list[str] | None) -> list[str]:
    if stages is None:
        return list(DEFAULT_SESSION_STAGES)
    raw: list[str] = []
    if isinstance(stages, str):
        raw = [part.strip() for part in stages.split(",")]
    else:
        for item in stages:
            raw.extend(part.strip() for part in item.split(","))
    result: list[str] = []
    for stage in raw:
        if not stage:
            continue
        key = stage.lower()
        if key not in SESSION_STAGE_DEFAULTS:
            allowed = ", ".join(SESSION_STAGE_DEFAULTS)
            raise ValueError(f"unknown agent-session stage: {stage}; expected one of {allowed}")
        if key not in result:
            result.append(key)
    if not result:
        raise ValueError("agent-session requires at least one stage.")
    return result


def default_session_id(*, book: str, chapter: str | None) -> str:
    chapter_part = f"_ch_{chapter}" if chapter else ""
    return slugify_session_id(f"{book}{chapter_part}_session")


def resolve_session_output_dir(project: Path, out_dir: str | None, session_id: str) -> Path:
    selected = out_dir or f"00_management/agent_sessions/{session_id}"
    candidate = Path(selected).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def session_run_dir(session_id: str, stage: str, *, book: str, chapter: str | None) -> str:
    chapter_part = f"_ch_{chapter}" if chapter else ""
    return f"00_management/agent_runs/{session_id}_{stage}_{book}{chapter_part}"


def status_for_run(project: Path, run_dir: str) -> tuple[str, int]:
    path = project / run_dir
    if not path.exists():
        return "planned", 0
    inbox = build_agent_inbox(path)
    if inbox.ready_count > 0:
        return "ready_for_review", inbox.ready_count
    if inbox.needs_attention_count > 0:
        return "needs_attention", 0
    if inbox.awaiting_count > 0:
        return "awaiting_output", 0
    return inbox.status, inbox.ready_count


def build_session_steps(project: Path, *, session_id: str, book: str, chapter: str | None, stages: list[str]) -> tuple[list[AgentSessionStep], int]:
    steps: list[AgentSessionStep] = []
    ready_count = 0
    for stage in stages:
        config = SESSION_STAGE_DEFAULTS[stage]
        run_dir = session_run_dir(session_id, stage, book=book, chapter=chapter)
        status, ready = status_for_run(project, run_dir)
        ready_count += ready
        command_parts = [
            "fictionops",
            str(config["command"]),
            ".",
            "--book",
            book,
        ]
        if chapter:
            command_parts.extend(["--chapter", chapter])
        command_parts.extend(["--out-dir", run_dir])
        steps.append(
            AgentSessionStep(
                stage=stage,
                command=str(config["command"]),
                role=str(config["role"]),
                task=str(config["task"]),
                run_dir=run_dir,
                status=status,
                next_command=" ".join(command_parts),
            )
        )
    return steps, ready_count


def session_status(steps: list[AgentSessionStep]) -> str:
    if any(step.status == "needs_attention" for step in steps):
        return "needs_attention"
    if steps and all(step.status == "completed" for step in steps):
        return "completed"
    if any(step.status == "ready_for_review" for step in steps):
        return "waiting_for_review"
    if any(step.status != "planned" for step in steps):
        return "in_progress"
    return "planned"


def format_agent_session_readme(report: AgentSessionReport) -> str:
    lines = [
        "# FictionOps Agent Session",
        "",
        f"- Session ID: `{report.session_id}`",
        f"- Goal: {report.goal}",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Status: `{report.status}`",
        "",
        "## Steps",
        "",
        "| Stage | Status | Role | Run Dir | Next Command |",
        "| --- | --- | --- | --- | --- |",
    ]
    for step in report.steps:
        lines.append(f"| `{step.stage}` | `{step.status}` | `{step.role}` | `{step.run_dir}` | `{step.next_command}` |")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def session_payload(report: AgentSessionReport) -> dict[str, object]:
    return {
        "schema": "fictionops.agent_session.v1",
        **asdict(report),
    }


def write_agent_session(report: AgentSessionReport, *, force: bool) -> list[AgentSessionFile]:
    output_dir = Path(report.output_dir)
    files = {
        "readme": output_dir / "README.md",
        "session": output_dir / "session.json",
    }
    if not force:
        existing = [path for path in files.values() if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    output_dir.mkdir(parents=True, exist_ok=True)
    files["readme"].write_text(format_agent_session_readme(report), encoding="utf-8", newline="\n")
    files["session"].write_text(json.dumps(session_payload(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return [AgentSessionFile(kind=kind, path=str(path), written=True) for kind, path in files.items()]


def next_actions_for_agent_session(report: AgentSessionReport) -> list[str]:
    for step in report.steps:
        if step.status == "planned":
            return [f"Run `{step.next_command}` to prepare the {step.stage} stage."]
        if step.status == "awaiting_output":
            return [f"Run `fictionops agent-exec {step.run_dir} --runner ...`, then inspect with `fictionops agent-inbox {step.run_dir}`."]
        if step.status == "ready_for_review":
            return [f"Review staged output with `fictionops agent-inbox {step.run_dir}` before continuing the session."]
        if step.status == "needs_attention":
            return [f"Fix `fictionops agent-inbox {step.run_dir}` issues before continuing the session."]
    return ["All planned session stages have run; update retrospectives or gates before closing the work."]


def build_agent_session(
    project: Path,
    *,
    book: str = "book_01",
    chapter: str | None = None,
    goal: str | None = None,
    session_id: str | None = None,
    stages: str | list[str] | None = None,
    out_dir: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> AgentSessionReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"agent-session requires a FictionOps project directory: {project}")
    target = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter) if chapter else None
    selected_session_id = slugify_session_id(session_id) if session_id else default_session_id(book=book_id, chapter=chapter_number)
    selected_goal = goal or f"Coordinate staged AI work for {book_id} {chapter_number or ''}".strip()
    selected_stages = normalize_session_stages(stages)
    output_dir = resolve_session_output_dir(target, out_dir, selected_session_id)
    steps, ready_count = build_session_steps(target, session_id=selected_session_id, book=book_id, chapter=chapter_number, stages=selected_stages)
    report = AgentSessionReport(
        target=str(target),
        session_id=selected_session_id,
        goal=selected_goal,
        book=book_id,
        chapter=chapter_number,
        output_dir=str(output_dir),
        dry_run=dry_run,
        written=False,
        status=session_status(steps),
        step_count=len(steps),
        ready_count=ready_count,
        files=[],
        steps=steps,
        next_actions=[],
    )
    report.next_actions = next_actions_for_agent_session(report)
    if not dry_run:
        report.files = write_agent_session(report, force=force)
        report.written = True
    else:
        report.files = [
            AgentSessionFile(kind="readme", path=str(output_dir / "README.md"), written=False),
            AgentSessionFile(kind="session", path=str(output_dir / "session.json"), written=False),
        ]
    return report


def render_agent_session(report: AgentSessionReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(session_payload(report), ensure_ascii=False, indent=2)
    return format_agent_session(report)


def format_agent_session(report: AgentSessionReport) -> str:
    lines = [
        "# FictionOps Agent Session",
        "",
        f"- Session ID: `{report.session_id}`",
        f"- Goal: {report.goal}",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Output dir: `{report.output_dir}`",
        f"- Status: `{report.status}`",
        f"- Written: {'yes' if report.written else 'no'}",
        "",
        "## Steps",
        "",
        "| Stage | Status | Command | Run Dir |",
        "| --- | --- | --- | --- |",
    ]
    for step in report.steps:
        lines.append(f"| `{step.stage}` | `{step.status}` | `{step.next_command}` | `{step.run_dir}` |")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
