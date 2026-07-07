from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .markdown import display_path, is_cjk, looks_placeholder, safe_cell
from .models import PostDraftIssue, PostDraftReport
from .new_chapter import chapter_paths, normalize_chapter_number
from .plan_chapter import normalize_book_for_plan
from .retrospective import extract_actual_chars, extract_sync_items


def count_nonspace(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def count_cjk(text: str) -> int:
    return sum(1 for char in text if is_cjk(char))


def resolve_post_draft_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_post_draft(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def issue(severity: str, code: str, path: Path, base: Path, message: str) -> PostDraftIssue:
    return PostDraftIssue(
        severity=severity,
        code=code,
        path=display_path(path, base),
        message=message,
    )


def post_draft_status(issues: list[PostDraftIssue]) -> tuple[str, bool]:
    codes = {item.code for item in issues}
    if "missing_chapter" in codes or "placeholder_chapter" in codes:
        return "needs_draft", False
    if "missing_chapter_engine" in codes or "placeholder_chapter_engine" in codes:
        return "needs_engine", False
    if "missing_chapter_retrospective" in codes or "placeholder_chapter_retrospective" in codes:
        return "needs_retrospective", False
    if "open_sync_item" in codes:
        return "sync_needed", False
    return "ready_for_review", True


def next_actions_for_status(report: PostDraftReport | None, issues: list[PostDraftIssue], *, book: str, chapter: str) -> list[str]:
    codes = {item.code for item in issues}
    actions: list[str] = []
    if "missing_chapter" in codes:
        actions.append(f"Run `fictionops new-chapter . --book {book} --chapter {chapter}` or create the missing draft file.")
    if "placeholder_chapter" in codes:
        actions.append("Expand the draft beyond the placeholder before treating it as written.")
    if "missing_chapter_engine" in codes or "placeholder_chapter_engine" in codes:
        actions.append(f"Run `fictionops plan-chapter . --book {book} --chapter {chapter}` and refill the chapter engine.")
        actions.append(f"Run `fictionops draft-brief . --book {book} --chapter {chapter}` before rewriting.")
    if "missing_chapter_retrospective" in codes or "placeholder_chapter_retrospective" in codes:
        actions.append(f"Fill `06_drafts/{book}/revision_notes/ch_{chapter}_retrospective.md` with actual residue and sync notes.")
    if "open_sync_item" in codes:
        actions.append("Sync recorded items to character arcs, information table, echo table, book outline, or archive before broad handoff.")
        actions.append(f"Run `fictionops revision-plan . --book {book}` to turn open follow-up into ordered tasks.")
    if not actions:
        actions.append(f"Run review gates: `fictionops context-pack . --task review --book {book} --chapter {chapter}`.")
        actions.append("Then run information, character, continuity, echo, and style review as needed.")
    return actions


def build_post_draft_report(
    project: Path,
    *,
    book: str = "book_01",
    chapter: str,
    min_chapter_chars: int = 200,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> PostDraftReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"post-draft requires a FictionOps project directory: {project}")

    resolved = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter)
    paths = chapter_paths(resolved, book=book_id, chapter_number=chapter_number)
    chapter_file = paths["chapter"]
    engine_file = paths["engine"]
    retrospective_file = paths["retrospective"]

    chapter_exists = chapter_file.exists() and chapter_file.is_file()
    engine_exists = engine_file.exists() and engine_file.is_file()
    retrospective_exists = retrospective_file.exists() and retrospective_file.is_file()

    chapter_text = chapter_file.read_text(encoding="utf-8") if chapter_exists else ""
    engine_text = engine_file.read_text(encoding="utf-8") if engine_exists else ""
    retrospective_text = retrospective_file.read_text(encoding="utf-8") if retrospective_exists else ""

    chapter_placeholder = True if not chapter_exists else looks_placeholder(chapter_text, min_chars=min_chapter_chars)
    engine_placeholder = False if not engine_exists else looks_placeholder(engine_text)
    retrospective_placeholder = False if not retrospective_exists else looks_placeholder(retrospective_text)
    sync_items = extract_sync_items(retrospective_text) if retrospective_exists else []
    actual_chars = extract_actual_chars(retrospective_text) if retrospective_exists else ""

    issues: list[PostDraftIssue] = []
    if not chapter_exists:
        issues.append(issue("P1", "missing_chapter", chapter_file, resolved, "Chapter draft file is missing."))
    elif chapter_placeholder:
        issues.append(
            issue(
                "P1",
                "placeholder_chapter",
                chapter_file,
                resolved,
                f"Chapter draft still looks like a placeholder or is below {min_chapter_chars} nonspace characters.",
            )
        )
    if not engine_exists:
        issues.append(issue("P2", "missing_chapter_engine", engine_file, resolved, "Chapter engine is missing."))
    elif engine_placeholder:
        issues.append(issue("P3", "placeholder_chapter_engine", engine_file, resolved, "Chapter engine still looks like a template."))
    if not retrospective_exists:
        issues.append(
            issue("P2", "missing_chapter_retrospective", retrospective_file, resolved, "Chapter retrospective is missing.")
        )
    elif retrospective_placeholder:
        issues.append(
            issue(
                "P2",
                "placeholder_chapter_retrospective",
                retrospective_file,
                resolved,
                "Chapter retrospective still looks like a template.",
            )
        )
    for item in sync_items:
        issues.append(issue("P3", "open_sync_item", retrospective_file, resolved, item))

    status, ready = post_draft_status(issues)
    output_path = resolve_post_draft_output_path(resolved, out) if out else None
    report = PostDraftReport(
        target=str(resolved),
        book=book_id,
        chapter=chapter_number,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        min_chapter_chars=min_chapter_chars,
        status=status,
        ready=ready,
        chapter_file=str(chapter_file),
        engine_file=str(engine_file),
        retrospective_file=str(retrospective_file),
        chapter_exists=chapter_exists,
        chapter_placeholder=chapter_placeholder,
        engine_exists=engine_exists,
        engine_placeholder=engine_placeholder,
        retrospective_exists=retrospective_exists,
        retrospective_placeholder=retrospective_placeholder,
        chapter_chars=len(chapter_text),
        chapter_nonspace_chars=count_nonspace(chapter_text),
        chapter_cjk_chars=count_cjk(chapter_text),
        retrospective_actual_chars=actual_chars,
        sync_items=sync_items,
        issue_count=len(issues),
        next_actions=[],
        issues=issues,
    )
    report.next_actions = next_actions_for_status(report, issues, book=book_id, chapter=chapter_number)
    if output_path and not dry_run:
        write_post_draft(output_path, render_post_draft_report(report, "markdown"), force=force)
        report.written = True
    return report


def render_post_draft_report(report: PostDraftReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_post_draft_report(report)


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def format_post_draft_report(report: PostDraftReport) -> str:
    lines = [
        "# FictionOps Post-Draft Gate",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter}`",
        f"- Status: `{report.status}`",
        f"- Ready: {yes_no(report.ready)}",
        f"- Min chapter chars: {report.min_chapter_chars}",
        f"- Issues: {report.issue_count}",
        "",
        "## Files",
        "",
        "| Kind | Exists | Placeholder | Chars | Path |",
        "| --- | --- | --- | ---: | --- |",
        f"| Chapter | {yes_no(report.chapter_exists)} | {yes_no(report.chapter_placeholder)} | {report.chapter_nonspace_chars} | `{safe_cell(report.chapter_file)}` |",
        f"| Engine | {yes_no(report.engine_exists)} | {yes_no(report.engine_placeholder)} | - | `{safe_cell(report.engine_file)}` |",
        f"| Retrospective | {yes_no(report.retrospective_exists)} | {yes_no(report.retrospective_placeholder)} | {safe_cell(report.retrospective_actual_chars)} | `{safe_cell(report.retrospective_file)}` |",
        "",
        "## Sync Items",
        "",
    ]
    if report.sync_items:
        for item in report.sync_items:
            lines.append(f"- {item}")
    else:
        lines.append("- None recorded.")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(f"| {item.severity} | `{item.code}` | `{safe_cell(item.path)}` | {safe_cell(item.message)} |")
    else:
        lines.append("No post-draft blockers found.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
