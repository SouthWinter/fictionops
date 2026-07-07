from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .chapter_wave import build_chapter_wave_report
from .character_audit import build_character_audit_report
from .constants import DEFAULT_WATCH_TERMS
from .continuity_audit import build_continuity_report
from .echo_audit import build_echo_report
from .information_audit import build_info_report
from .markdown import display_path, safe_cell
from .models import ReviewGateCheck, ReviewGateIssue, ReviewGateReport
from .new_chapter import chapter_paths, normalize_chapter_number
from .plan_chapter import normalize_book_for_plan
from .post_draft import build_post_draft_report
from .style_audit import build_style_audit_report


BLOCKING_SEVERITIES = {"P0", "P1", "P2"}


def severity_blocks(severity: str) -> bool:
    return (severity or "P4").upper() in BLOCKING_SEVERITIES


def resolve_review_gate_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_review_gate(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def gate_issue(
    *,
    source: str,
    issue: object,
    default_subject: str = "-",
    default_path: str = "-",
) -> ReviewGateIssue:
    return ReviewGateIssue(
        severity=str(getattr(issue, "severity", "P4") or "P4"),
        source=source,
        code=str(getattr(issue, "code", "issue") or "issue"),
        subject=str(
            getattr(issue, "chapter", "")
            or getattr(issue, "item", "")
            or getattr(issue, "thread", "")
            or getattr(issue, "character", "")
            or default_subject
        ),
        path=str(getattr(issue, "path", "") or default_path),
        message=str(getattr(issue, "message", "")),
    )


def chapter_specific(path_or_message: str, chapter: str) -> bool:
    needle = f"ch_{chapter}"
    compact = path_or_message.replace("\\", "/")
    try:
        chapter_int = int(chapter)
    except ValueError:
        localized = ""
    else:
        localized = f"\u7b2c{chapter_int}\u7ae0"
    return needle in compact or f"/{chapter}" in compact or f"_{chapter}" in compact or bool(localized and localized in compact)


def select_gate_issues(
    *,
    source: str,
    issues: list[object],
    chapter: str,
    include_notes: bool = True,
) -> list[ReviewGateIssue]:
    selected: list[ReviewGateIssue] = []
    for item in issues:
        candidate = gate_issue(source=source, issue=item)
        if severity_blocks(candidate.severity):
            selected.append(candidate)
            continue
        if include_notes and chapter_specific(candidate.path + " " + candidate.message + " " + candidate.subject, chapter):
            selected.append(candidate)
    return selected


def check_from_issues(name: str, command: str, issues: list[ReviewGateIssue], summary: str) -> ReviewGateCheck:
    blocking = sum(1 for item in issues if severity_blocks(item.severity))
    status = "pass" if not issues else ("blocked" if blocking else "notes")
    return ReviewGateCheck(
        name=name,
        source_command=command,
        status=status,
        issue_count=len(issues),
        blocking_issue_count=blocking,
        summary=summary,
    )


def style_gate_issues(style_report, *, chapter_path: str) -> list[ReviewGateIssue]:
    issues: list[ReviewGateIssue] = []
    chapter_name = Path(chapter_path).name
    for item in style_report.files:
        if item.path != chapter_path and not chapter_path.endswith(item.path) and Path(item.path).name != chapter_name:
            continue
        if item.watch_total >= 12:
            issues.append(
                ReviewGateIssue(
                    severity="P4",
                    source="audit-style",
                    code="style_watch_density",
                    subject="-",
                    path=item.path,
                    message=f"Watched style terms appear {item.watch_total} times in this chapter.",
                )
            )
        for opening in item.repeated_openings:
            issues.append(
                ReviewGateIssue(
                    severity="P4",
                    source="audit-style",
                    code="repeated_sentence_opening",
                    subject=opening.item,
                    path=item.path,
                    message=f"Sentence opening repeats {opening.count} times.",
                )
            )
    return issues


def next_actions(status: str, issues: list[ReviewGateIssue], *, book: str, chapter: str) -> list[str]:
    if status == "needs_post_draft":
        return [f"Run or fix `fictionops post-draft . --book {book} --chapter {chapter}` before broad review."]
    blocking = [item for item in issues if severity_blocks(item.severity)]
    if blocking:
        sources = sorted({item.source for item in blocking})
        return [
            "Resolve blocking review issues from: " + ", ".join(sources) + ".",
            f"Run `fictionops revision-plan . --book {book}` after fixing the blocking items.",
        ]
    if issues:
        return [
            "Review non-blocking notes before prose polish.",
            f"Run `fictionops revision-plan . --book {book}` if the notes should become tracked tasks.",
        ]
    return [
        "Proceed to targeted revision or style polish.",
        f"After revision, rerun `fictionops review-gate . --book {book} --chapter {chapter}`.",
    ]


def build_review_gate(
    project: Path,
    *,
    book: str = "book_01",
    chapter: str,
    min_chapter_chars: int = 200,
    pattern: str = "**/*.md",
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> ReviewGateReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"review-gate requires a FictionOps project directory: {project}")

    resolved = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter)
    chapter_file = chapter_paths(resolved, book=book_id, chapter_number=chapter_number)["chapter"]
    chapter_display = display_path(chapter_file, resolved)

    post_draft = build_post_draft_report(
        resolved,
        book=book_id,
        chapter=chapter_number,
        min_chapter_chars=min_chapter_chars,
        out=None,
        force=False,
        dry_run=True,
    )
    continuity = build_continuity_report(resolved, pattern=pattern, skip_standard=False, min_chapter_chars=min_chapter_chars)
    information = build_info_report(resolved, pattern=pattern, table_path=None, scan_text=True)
    characters = build_character_audit_report(resolved, pattern=pattern)
    echoes = build_echo_report(resolved, pattern=pattern, table_path=None, scan_text=True, stale_after=8)
    style = build_style_audit_report(chapter_file if chapter_file.exists() else resolved, all_markdown=False, pattern=pattern, watch_terms=DEFAULT_WATCH_TERMS, top=12, min_repeat=3)
    wave_target = resolved / "06_drafts" / book_id
    wave = build_chapter_wave_report(wave_target if wave_target.exists() else resolved, all_markdown=False, pattern=pattern, metric="nonspace")

    issues: list[ReviewGateIssue] = []
    issues.extend(select_gate_issues(source="post-draft", issues=post_draft.issues, chapter=chapter_number))
    issues.extend(select_gate_issues(source="audit-continuity", issues=continuity.issues, chapter=chapter_number))
    issues.extend(select_gate_issues(source="audit-info", issues=information.issues, chapter=chapter_number))
    issues.extend(select_gate_issues(source="audit-characters", issues=characters.issues, chapter=chapter_number))
    issues.extend(select_gate_issues(source="audit-echoes", issues=echoes.issues, chapter=chapter_number))
    issues.extend(style_gate_issues(style, chapter_path=chapter_display if chapter_file.exists() else display_path(resolved, resolved)))
    issues.extend(select_gate_issues(source="audit-wave", issues=wave.issues, chapter=chapter_number, include_notes=True))

    checks = [
        check_from_issues("Post-draft gate", "post-draft", [item for item in issues if item.source == "post-draft"], post_draft.status),
        check_from_issues("Continuity", "audit-continuity", [item for item in issues if item.source == "audit-continuity"], f"{continuity.chapter_count} chapters checked."),
        check_from_issues("Information boundary", "audit-info", [item for item in issues if item.source == "audit-info"], f"{information.item_count} information items checked."),
        check_from_issues("Character memory", "audit-characters", [item for item in issues if item.source == "audit-characters"], f"{characters.character_count} indexed characters checked."),
        check_from_issues("Foreshadowing echoes", "audit-echoes", [item for item in issues if item.source == "audit-echoes"], f"{echoes.thread_count} echo threads checked."),
        check_from_issues("Style", "audit-style", [item for item in issues if item.source == "audit-style"], f"{style.file_count} chapter file(s) checked."),
        check_from_issues("Chapter wave", "audit-wave", [item for item in issues if item.source == "audit-wave"], f"{wave.file_count} chapter file(s) checked."),
    ]
    blocking_count = sum(1 for item in issues if severity_blocks(item.severity))
    if not post_draft.ready:
        status = "needs_post_draft"
        ready = False
    elif blocking_count:
        status = "needs_review_fixes"
        ready = False
    elif issues:
        status = "review_notes"
        ready = True
    else:
        status = "review_passed"
        ready = True

    output_path = resolve_review_gate_output_path(resolved, out) if out else None
    report = ReviewGateReport(
        target=str(resolved),
        book=book_id,
        chapter=chapter_number,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        status=status,
        ready=ready,
        issue_count=len(issues),
        blocking_issue_count=blocking_count,
        checks=checks,
        issues=issues,
        next_actions=next_actions(status, issues, book=book_id, chapter=chapter_number),
        post_draft=post_draft,
    )
    if output_path and not dry_run:
        write_review_gate(output_path, render_review_gate(report, "markdown"), force=force)
        report.written = True
    return report


def render_review_gate(report: ReviewGateReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_review_gate(report)


def format_review_gate(report: ReviewGateReport) -> str:
    lines = [
        "# FictionOps Review Gate",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Issues: {report.issue_count}",
        f"- Blocking issues: {report.blocking_issue_count}",
        "",
        "## Checks",
        "",
        "| Check | Status | Issues | Blocking | Source | Summary |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            "| "
            + " | ".join(
                [
                    safe_cell(check.name),
                    safe_cell(check.status),
                    str(check.issue_count),
                    str(check.blocking_issue_count),
                    f"`{safe_cell(check.source_command)}`",
                    safe_cell(check.summary),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Source | Code | Subject | Path | Message |", "| --- | --- | --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(item.severity),
                        safe_cell(item.source),
                        f"`{safe_cell(item.code)}`",
                        safe_cell(item.subject),
                        f"`{safe_cell(item.path)}`",
                        safe_cell(item.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No review-gate issues found.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
