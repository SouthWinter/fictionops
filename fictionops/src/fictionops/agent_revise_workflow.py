from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .agent_exec import DEFAULT_AGENT_EXEC_OUTPUT, build_agent_exec
from .agent_inbox import build_agent_inbox
from .model_config import build_model_config_report
from .models import AgentExecReport, AgentInboxReport
from .review_workflow import build_review_workflow_report, render_review_workflow_report


REVISION_CONTRACT = """# FictionOps Revision Contract

You are revising a long-form fiction chapter from a staged review workflow.

## Goal

Produce a revised version of the source chapter that addresses the review workflow's highest-impact prose-pattern issues while preserving story continuity.

## Must Preserve

- Preserve all plot events, character intentions, point of view, chronology, names, places, objects, and information boundaries.
- Preserve ambiguity, silence, and withheld explanation when the source relies on them.
- Preserve functional repetition when it carries theme, pressure, rhythm, or character perception.
- Preserve the chapter's rough length and scene order unless a sentence-level adjustment requires a local move.

## Must Improve

- Reduce low-value repeated negation patterns only where action, object state, gesture, silence, or viewpoint perception can carry the same meaning.
- Reduce default sensory fields, such as cold/heat clusters, only where the image is not doing scene work.
- Reduce explanatory similes and turn signals only where the prose is translating what the scene already shows.
- Keep the language alive and varied. Do not flatten the author's style into generic smoothness.

## Must Not Do

- Do not add new lore, new motives, new facts, new foreshadowing, or new exposition.
- Do not solve mysteries that the chapter intentionally leaves open.
- Do not optimize word counts mechanically.
- Do not output commentary, diagnosis, bullet points, or a summary.

## Output

Write only the revised chapter text to stdout. FictionOps will save it as staged output and will not apply it automatically.
"""


@dataclass
class AgentReviseWorkflowFile:
    kind: str
    path: str
    written: bool


@dataclass
class AgentReviseWorkflowReport:
    command: str
    target: str
    chapter_file: str
    review_file: str | None
    run_dir: str
    role: str
    task: str
    provider: str
    model: str
    prepared: bool
    executed: bool
    inbox_status: str | None
    ready_count: int
    output_name: str
    stop_reason: str
    files: list[AgentReviseWorkflowFile]
    staged_outputs: list[dict[str, object]]
    safety: dict[str, object]
    next_actions: list[str]
    agent_exec: AgentExecReport | None
    inbox: AgentInboxReport | None


def safe_run_name(chapter_file: Path) -> str:
    stem = chapter_file.stem.strip() or "chapter"
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", stem)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("_")
    return f"revise_workflow_{cleaned or 'chapter'}"


def find_project_anchor(path: Path) -> Path:
    start = path if path.is_dir() else path.parent
    for current in [start, *start.parents]:
        if (current / "00_management").is_dir() or (current / "00_总纲与管理").is_dir():
            return current
    return start


def default_agent_revise_workflow_dir(chapter_file: Path) -> Path:
    anchor = find_project_anchor(chapter_file)
    if (anchor / "00_management").is_dir():
        base = anchor / "00_management" / "agent_runs"
    elif (anchor / "00_总纲与管理").is_dir():
        base = anchor / "00_总纲与管理" / "agent_runs"
    else:
        base = chapter_file.parent / ".fictionops_agent_runs"
    return (base / safe_run_name(chapter_file)).resolve()


def resolve_agent_revise_workflow_dir(chapter_file: Path, out_dir: str | None) -> Path:
    if not out_dir:
        return default_agent_revise_workflow_dir(chapter_file)
    candidate = Path(out_dir).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (find_project_anchor(chapter_file) / candidate).resolve()


def read_or_build_review(chapter_file: Path, review_file: Path | None) -> tuple[str, str | None]:
    if review_file is None:
        report = build_review_workflow_report(chapter_file, top_lines=80)
        return render_review_workflow_report(report, "markdown"), None
    if not review_file.exists():
        raise FileNotFoundError(f"review workflow file does not exist: {review_file}")
    if not review_file.is_file():
        raise ValueError(f"--review must point to a file: {review_file}")
    return review_file.read_text(encoding="utf-8"), str(review_file.resolve())


def build_revision_prompt(*, chapter_file: Path, review_file: str | None) -> str:
    review_source = review_file or "generated from the source chapter during this command"
    return "\n".join(
        [
            "# FictionOps Agent Revision Prompt",
            "",
            "Revise the chapter using the bundled review workflow and revision contract.",
            "",
            "## Inputs",
            "",
            f"- Source chapter: `source_chapter.md` copied from `{chapter_file}`",
            f"- Review workflow: `review_workflow.md` ({review_source})",
            "- Revision contract: `revision_contract.md`",
            "",
            "## Task",
            "",
            "Return a staged revised chapter. Treat the review workflow as a queue of issues to triage, not as a command to erase all repeated words.",
            "",
            "Prioritize P1/P2 pattern families, but keep any repeated phrase that has scene, rhythm, viewpoint, or thematic function.",
            "",
            "## Output Contract",
            "",
            "Write only the revised chapter text. Do not include markdown fences, a change log, comments, or analysis.",
        ]
    ).rstrip() + "\n"


def build_revision_context(
    *,
    chapter_file: Path,
    review_text: str,
    chapter_text: str,
    review_file: str | None,
    max_chapter_chars: int,
    max_review_chars: int,
) -> str:
    clipped_chapter = chapter_text[:max_chapter_chars]
    clipped_review = review_text[:max_review_chars]
    chapter_note = "" if len(chapter_text) <= max_chapter_chars else f"\n\n[Chapter clipped at {max_chapter_chars} characters in context_pack.md; full text is in source_chapter.md.]"
    review_note = "" if len(review_text) <= max_review_chars else f"\n\n[Review clipped at {max_review_chars} characters in context_pack.md; full text is in review_workflow.md.]"
    lines = [
        "# FictionOps Revision Context Pack",
        "",
        "This pack is self-contained for an external revision runner.",
        "",
        "## Files In This Bundle",
        "",
        "- `source_chapter.md`: full source chapter",
        "- `review_workflow.md`: full review workflow report",
        "- `revision_contract.md`: safety and output contract",
        "- `prompt.md`: role/task prompt",
        "",
        "## Source",
        "",
        f"- Chapter file: `{chapter_file}`",
        f"- Review file: `{review_file or 'generated inside this bundle'}`",
        "",
        "## Revision Contract",
        "",
        REVISION_CONTRACT.rstrip(),
        "",
        "## Review Workflow",
        "",
        clipped_review.rstrip(),
        review_note,
        "",
        "## Source Chapter",
        "",
        clipped_chapter.rstrip(),
        chapter_note,
    ]
    return "\n".join(lines).rstrip() + "\n"


def request_payload(
    *,
    chapter_file: Path,
    review_file: str | None,
    run_dir: Path,
    role: str,
    provider: str,
    model: str,
    files: list[AgentReviseWorkflowFile],
) -> dict[str, object]:
    return {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(chapter_file.resolve()),
        "role": role,
        "role_name": "Style Revision Agent",
        "task": "review",
        "book": "-",
        "chapter": chapter_file.stem,
        "provider": provider,
        "model": model,
        "model_config_file": None,
        "source_chapter_file": str(chapter_file.resolve()),
        "review_workflow_file": review_file,
        "run_dir": str(run_dir),
        "files": [asdict(item) for item in files],
        "next_actions": [
            "Run `fictionops agent-exec <run_dir> --runner ...` to call a model-backed runner.",
            "Inspect staged output with `fictionops agent-inbox <run_dir>` before applying any text.",
            "After accepting edits manually, rerun `fictionops review-workflow <chapter>` and compare recheck targets.",
        ],
        "safety": agent_revise_workflow_safety(),
    }


def agent_revise_workflow_safety() -> dict[str, object]:
    return {
        "calls_model": False,
        "stores_api_keys": False,
        "overwrites_manuscript": False,
        "writes_staging_output": True,
        "requires_human_apply": True,
        "accepts_direct_chapter_file": True,
    }


def planned_files(run_dir: Path) -> dict[str, Path]:
    return {
        "readme": run_dir / "README.md",
        "request": run_dir / "request.json",
        "prompt": run_dir / "prompt.md",
        "context_pack": run_dir / "context_pack.md",
        "source_chapter": run_dir / "source_chapter.md",
        "review_workflow": run_dir / "review_workflow.md",
        "revision_contract": run_dir / "revision_contract.md",
    }


def write_bundle(
    *,
    run_dir: Path,
    chapter_file: Path,
    review_file: str | None,
    chapter_text: str,
    review_text: str,
    role: str,
    provider: str,
    model: str,
    force: bool,
    max_chapter_chars: int,
    max_review_chars: int,
) -> list[AgentReviseWorkflowFile]:
    files = planned_files(run_dir)
    if not force:
        existing = [path for path in files.values() if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    run_dir.mkdir(parents=True, exist_ok=True)
    file_reports = [AgentReviseWorkflowFile(kind=kind, path=str(path), written=True) for kind, path in files.items()]
    prompt = build_revision_prompt(chapter_file=chapter_file, review_file=review_file)
    context = build_revision_context(
        chapter_file=chapter_file,
        review_text=review_text,
        chapter_text=chapter_text,
        review_file=review_file,
        max_chapter_chars=max_chapter_chars,
        max_review_chars=max_review_chars,
    )
    readme = "\n".join(
        [
            "# FictionOps Agent Revision Workflow Bundle",
            "",
            f"- Source chapter: `{chapter_file}`",
            f"- Review workflow: `{review_file or 'generated from source chapter'}`",
            f"- Role: `{role}`",
            f"- Provider: `{provider}`",
            f"- Model: `{model}`",
            "",
            "## Rule",
            "",
            "This bundle lets an external model revise a chapter from a review workflow. It never applies output to the manuscript automatically.",
            "",
            "## Next Actions",
            "",
            f"- Run `fictionops agent-exec {run_dir} --runner ...`.",
            f"- Inspect staged output with `fictionops agent-inbox {run_dir}`.",
            "- Apply accepted text manually, then rerun `fictionops review-workflow` on the accepted chapter.",
        ]
    ).rstrip() + "\n"
    files["readme"].write_text(readme, encoding="utf-8", newline="\n")
    files["prompt"].write_text(prompt, encoding="utf-8", newline="\n")
    files["context_pack"].write_text(context, encoding="utf-8", newline="\n")
    files["source_chapter"].write_text(chapter_text.rstrip() + "\n", encoding="utf-8", newline="\n")
    files["review_workflow"].write_text(review_text.rstrip() + "\n", encoding="utf-8", newline="\n")
    files["revision_contract"].write_text(REVISION_CONTRACT.rstrip() + "\n", encoding="utf-8", newline="\n")
    payload = request_payload(
        chapter_file=chapter_file,
        review_file=review_file,
        run_dir=run_dir,
        role=role,
        provider=provider,
        model=model,
        files=file_reports,
    )
    files["request"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return file_reports


def staged_outputs_from_inbox(inbox: AgentInboxReport) -> list[dict[str, object]]:
    staged: list[dict[str, object]] = []
    for run in inbox.runs:
        if not run.output_file:
            continue
        staged.append(
            {
                "run_dir": run.run_dir,
                "output_file": run.output_file,
                "role": run.role,
                "task": run.task,
                "chapter": run.chapter,
                "state": "revision",
                "review_required": True,
                "output_chars": run.output_chars,
            }
        )
    return staged


def next_actions_for_report(report: AgentReviseWorkflowReport) -> list[str]:
    if report.executed and report.ready_count > 0:
        return [
            f"Inspect staged revision with `fictionops agent-inbox {report.run_dir}`.",
            "Compare staged output against the source chapter before manually applying accepted text.",
            f"After applying accepted edits, rerun `fictionops review-workflow {report.chapter_file}`.",
        ]
    if report.executed:
        return [f"Inspect `{report.run_dir}` with `fictionops agent-inbox` before retrying."]
    return [
        f"Run a model-backed runner with `fictionops agent-exec {report.run_dir} --runner ...`.",
        f"Then inspect staged output with `fictionops agent-inbox {report.run_dir}`.",
    ]


def build_agent_revise_workflow(
    chapter: Path,
    *,
    review: Path | None = None,
    out_dir: str | None = None,
    role: str = "style-auditor",
    provider: str | None = None,
    model: str | None = None,
    runner: list[str] | None = None,
    output_name: str = DEFAULT_AGENT_EXEC_OUTPUT,
    timeout_seconds: int = 300,
    force: bool = False,
    force_output: bool = False,
    dry_run: bool = False,
    max_chapter_chars: int = 120000,
    max_review_chars: int = 50000,
) -> AgentReviseWorkflowReport:
    if not chapter.exists():
        raise FileNotFoundError(f"chapter file does not exist: {chapter}")
    if not chapter.is_file():
        raise ValueError(f"agent-revise-workflow requires a chapter file: {chapter}")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be greater than zero.")
    chapter_file = chapter.expanduser().resolve()
    run_dir = resolve_agent_revise_workflow_dir(chapter_file, out_dir)
    chapter_text = chapter_file.read_text(encoding="utf-8")
    review_text, review_file = read_or_build_review(chapter_file, review.expanduser().resolve() if review else None)

    anchor = find_project_anchor(chapter_file)
    model_config = build_model_config_report(anchor)
    selected_provider = provider or model_config.provider
    selected_model = model or model_config.audit_model
    file_reports = [AgentReviseWorkflowFile(kind=kind, path=str(path), written=False) for kind, path in planned_files(run_dir).items()]
    prepared = False
    executed = False
    agent_exec = None
    inbox = None
    staged_outputs: list[dict[str, object]] = []
    stop_reason = "agent_run_ready_for_runner"

    if not dry_run:
        file_reports = write_bundle(
            run_dir=run_dir,
            chapter_file=chapter_file,
            review_file=review_file,
            chapter_text=chapter_text,
            review_text=review_text,
            role=role,
            provider=selected_provider,
            model=selected_model,
            force=force,
            max_chapter_chars=max_chapter_chars,
            max_review_chars=max_review_chars,
        )
        prepared = True

    if runner:
        if dry_run:
            stop_reason = "dry_run_runner_not_executed"
        else:
            agent_exec = build_agent_exec(
                run_dir,
                command=runner,
                output_name=output_name,
                timeout_seconds=timeout_seconds,
                force=force_output or force,
                dry_run=False,
            )
            executed = True
            inbox = build_agent_inbox(run_dir, output_name=output_name)
            staged_outputs = staged_outputs_from_inbox(inbox)
            stop_reason = "staged_output_ready_for_review" if inbox.ready_count > 0 else "agent_output_needs_attention"

    report = AgentReviseWorkflowReport(
        command="agent-revise-workflow",
        target=str(chapter_file),
        chapter_file=str(chapter_file),
        review_file=review_file,
        run_dir=str(run_dir),
        role=role,
        task="review",
        provider=selected_provider,
        model=selected_model,
        prepared=prepared,
        executed=executed,
        inbox_status=inbox.status if inbox else None,
        ready_count=inbox.ready_count if inbox else 0,
        output_name=output_name,
        stop_reason=stop_reason,
        files=file_reports,
        staged_outputs=staged_outputs,
        safety=agent_revise_workflow_safety(),
        next_actions=[],
        agent_exec=agent_exec,
        inbox=inbox,
    )
    report.next_actions = next_actions_for_report(report)
    return report


def render_agent_revise_workflow(report: AgentReviseWorkflowReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"Unsupported agent-revise-workflow format: {output_format}")
    return format_agent_revise_workflow(report)


def format_agent_revise_workflow(report: AgentReviseWorkflowReport) -> str:
    lines = [
        "# FictionOps Agent Revise Workflow",
        "",
        f"- Chapter: `{report.chapter_file}`",
        f"- Review workflow: `{report.review_file or 'generated'}`",
        f"- Run dir: `{report.run_dir}`",
        f"- Role: `{report.role}`",
        f"- Provider: `{report.provider}`",
        f"- Model: `{report.model}`",
        f"- Prepared: {'yes' if report.prepared else 'no'}",
        f"- Executed runner: {'yes' if report.executed else 'no'}",
        f"- Inbox status: `{report.inbox_status or '-'}`",
        f"- Ready staged outputs: {report.ready_count}",
        f"- Stop reason: `{report.stop_reason}`",
        "",
        "## Safety",
        "",
        "- The source chapter is copied into the bundle.",
        "- Runner output is staged only and never applied to the manuscript automatically.",
        "- Human review is required before any accepted text replaces the source chapter.",
        "",
        "## Bundle Files",
        "",
    ]
    if report.files:
        lines.extend(["| Kind | Written | Path |", "| --- | --- | --- |"])
        for item in report.files:
            lines.append(f"| `{item.kind}` | {'yes' if item.written else 'no'} | `{item.path}` |")
    else:
        lines.append("No bundle files planned.")

    lines.extend(["", "## Staged Outputs", ""])
    if report.staged_outputs:
        lines.extend(["| State | Output | Chars |", "| --- | --- | --- |"])
        for item in report.staged_outputs:
            lines.append(f"| `{item['state']}` | `{item['output_file']}` | {item['output_chars']} |")
    else:
        lines.append("No staged output is ready yet.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
