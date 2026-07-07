from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .agent_prompt import build_agent_prompt, render_agent_prompt
from .context_pack import render_context_pack
from .draft_brief import build_draft_brief, render_draft_brief
from .model_config import build_model_config_report
from .models import AgentRunFile, AgentRunReport
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


def resolve_agent_run_output_dir(project: Path, out_dir: str) -> Path:
    candidate = Path(out_dir).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def model_for_task(*, task: str, role: str, model_config) -> str:
    if task == "draft" and role == "draft-writer":
        return model_config.drafting_model
    if task in {"review", "canon-sync"}:
        return model_config.audit_model
    return model_config.planning_model


def planned_bundle_files(output_dir: Path, *, include_draft_brief: bool) -> dict[str, Path]:
    files = {
        "readme": output_dir / "README.md",
        "request": output_dir / "request.json",
        "prompt": output_dir / "prompt.md",
        "context_pack": output_dir / "context_pack.md",
    }
    if include_draft_brief:
        files["draft_brief"] = output_dir / "draft_brief.md"
    return files


def request_payload(report: AgentRunReport) -> dict[str, object]:
    return {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": report.execution_mode,
        "target": report.target,
        "role": report.role,
        "role_name": report.role_name,
        "task": report.task,
        "book": report.book,
        "chapter": report.chapter,
        "provider": report.provider,
        "model": report.model,
        "model_config_file": report.model_config_file,
        "files": [asdict(item) for item in report.files],
        "next_actions": report.next_actions,
        "safety": {
            "calls_model": False,
            "stores_api_keys": False,
            "overwrites_manuscript": False,
            "requires_human_apply": True,
        },
    }


def format_agent_run_readme(report: AgentRunReport) -> str:
    lines = [
        "# FictionOps Agent Run Bundle",
        "",
        f"- Execution mode: `{report.execution_mode}`",
        f"- Role: `{report.role}` / {report.role_name}",
        f"- Task: `{report.task}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Provider: `{report.provider or '-'}`",
        f"- Model: `{report.model or '-'}`",
        "",
        "## Files",
        "",
        "| Kind | Path |",
        "| --- | --- |",
    ]
    for item in report.files:
        path = Path(item.path)
        lines.append(f"| `{item.kind}` | [`{path.name}`]({path.name}) |")

    lines.extend(
        [
            "",
            "## How To Use",
            "",
            "1. Read `request.json` for machine-readable task metadata.",
            "2. Send `prompt.md` plus the relevant context files to the chosen model or human collaborator.",
            "3. Write model output to a staging file; do not overwrite manuscript files directly.",
            "4. Run the suggested FictionOps gate commands before applying changes.",
            "",
            "## Next Actions",
            "",
        ]
    )
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def write_agent_run_bundle(report: AgentRunReport, *, force: bool) -> list[AgentRunFile]:
    if not report.output_dir:
        return []
    output_dir = Path(report.output_dir)
    bundle = planned_bundle_files(output_dir, include_draft_brief=report.draft_brief is not None)
    if not force:
        existing = [path for path in bundle.values() if path.exists()]
        if existing:
            raise FileExistsError(existing[0])

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle["readme"].write_text(format_agent_run_readme(report), encoding="utf-8", newline="\n")
    bundle["request"].write_text(json.dumps(request_payload(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    bundle["prompt"].write_text(render_agent_prompt(report.agent_prompt, "markdown"), encoding="utf-8", newline="\n")
    bundle["context_pack"].write_text(render_context_pack(report.context_pack, "markdown"), encoding="utf-8", newline="\n")
    if report.draft_brief is not None and "draft_brief" in bundle:
        bundle["draft_brief"].write_text(render_draft_brief(report.draft_brief, "markdown"), encoding="utf-8", newline="\n")
    return [AgentRunFile(kind=kind, path=str(path), written=True) for kind, path in bundle.items()]


def next_actions_for_agent_run(report: AgentRunReport) -> list[str]:
    actions = [
        "Use the generated bundle as the input boundary for a human or external model runner.",
        "Save model output to a staging file before applying it to FictionOps project memory.",
    ]
    if report.task == "draft" and report.chapter:
        actions.append(f"After drafting, run `fictionops post-draft . --book {report.book} --chapter {report.chapter}`.")
        actions.append(f"Then run `fictionops review-gate . --book {report.book} --chapter {report.chapter}`.")
    elif report.task == "review" and report.chapter:
        actions.append(f"After review, run `fictionops revision-plan . --book {report.book}` before applying broad rewrites.")
    elif report.task == "canon-sync":
        actions.append("After canon-sync output, update the relevant canon files and rerun `fictionops doctor .`.")
    else:
        actions.append(f"After handoff/planning output, run `fictionops workflow-plan . --stage {report.task} --book {report.book}` if the next stage is unclear.")
    return actions


def build_agent_run(
    project: Path,
    *,
    role: str,
    task: str | None = None,
    book: str = "book_01",
    chapter: str | None = None,
    out_dir: str | None = None,
    include_context_content: bool = True,
    max_chars_per_file: int = 6000,
    max_total_context_chars: int = 60000,
    force: bool = False,
    dry_run: bool = False,
) -> AgentRunReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"agent-run requires a FictionOps project directory: {project}")

    target = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter) if chapter else None
    model_config = build_model_config_report(target)
    agent_prompt = build_agent_prompt(
        target,
        role=role,
        task=task,
        book=book_id,
        chapter=chapter_number,
        include_context=True,
        include_context_content=include_context_content,
        max_chars_per_file=max_chars_per_file,
        max_total_context_chars=max_total_context_chars,
        out=None,
        force=False,
        dry_run=True,
    )
    context_pack = agent_prompt.context_pack
    if context_pack is None:
        raise ValueError("agent-run requires a generated context pack")

    draft_brief = None
    if agent_prompt.task == "draft" and chapter_number is not None:
        draft_brief = build_draft_brief(
            target,
            book=book_id,
            chapter=chapter_number,
            include_context_content=include_context_content,
            max_chars_per_file=max_chars_per_file,
            max_total_context_chars=max_total_context_chars,
            out=None,
            force=False,
            dry_run=True,
        )

    output_dir = resolve_agent_run_output_dir(target, out_dir) if out_dir else None
    planned_files = planned_bundle_files(output_dir, include_draft_brief=draft_brief is not None) if output_dir else {}
    files = [AgentRunFile(kind=kind, path=str(path), written=False) for kind, path in planned_files.items()]
    report = AgentRunReport(
        target=str(target),
        role=agent_prompt.role,
        role_name=agent_prompt.role_name,
        task=agent_prompt.task,
        book=book_id,
        chapter=chapter_number,
        output_dir=str(output_dir) if output_dir else None,
        dry_run=dry_run,
        written=False,
        execution_mode="prepare_only",
        provider=model_config.provider,
        model=model_for_task(task=agent_prompt.task, role=agent_prompt.role, model_config=model_config),
        model_config_file=model_config.config_file,
        model_config_issue_count=len(model_config.issues),
        prompt_file=str(planned_files.get("prompt")) if planned_files else None,
        context_pack_file=str(planned_files.get("context_pack")) if planned_files else None,
        draft_brief_file=str(planned_files.get("draft_brief")) if planned_files and "draft_brief" in planned_files else None,
        request_file=str(planned_files.get("request")) if planned_files else None,
        readme_file=str(planned_files.get("readme")) if planned_files else None,
        file_count=len(files),
        files=files,
        next_actions=[],
        agent_prompt=agent_prompt,
        context_pack=context_pack,
        draft_brief=draft_brief,
        model_config=model_config,
    )
    report.next_actions = next_actions_for_agent_run(report)
    if output_dir and not dry_run:
        report.files = write_agent_run_bundle(report, force=force)
        report.written = True
        report.file_count = len(report.files)
    return report


def render_agent_run(report: AgentRunReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_run(report)


def format_agent_run(report: AgentRunReport) -> str:
    lines = [
        "# FictionOps Agent Run",
        "",
        f"- Target: `{report.target}`",
        f"- Execution mode: `{report.execution_mode}`",
        f"- Role: `{report.role}` / {report.role_name}",
        f"- Task: `{report.task}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Provider: `{report.provider or '-'}`",
        f"- Model: `{report.model or '-'}`",
        f"- Output dir: `{report.output_dir or '-'}`",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Files: {report.file_count}",
        "",
        "## Rule",
        "",
        "This command prepares an agent task bundle. It does not call a model, store API keys, or overwrite manuscript files.",
        "",
        "## Bundle Files",
        "",
    ]
    if report.files:
        lines.extend(["| Kind | Written | Path |", "| --- | --- | --- |"])
        for item in report.files:
            lines.append(f"| `{item.kind}` | {'yes' if item.written else 'no'} | `{item.path}` |")
    else:
        lines.append("No bundle files planned. Pass `--out-dir` to write a bundle.")

    lines.extend(["", "## Model Config Issues", ""])
    if report.model_config.issues:
        lines.extend(["| Severity | Code | Field | Message |", "| --- | --- | --- | --- |"])
        for issue in report.model_config.issues:
            lines.append(f"| {issue.severity} | `{issue.code}` | `{issue.field}` | {issue.message} |")
    else:
        lines.append("No model configuration issues found.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
