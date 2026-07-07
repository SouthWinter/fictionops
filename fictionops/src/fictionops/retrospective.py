from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .audit_plan import collect_book_files
from .echo_audit import blankish
from .markdown import display_path, looks_placeholder, safe_cell
from .models import RetrospectiveChapter, RetrospectiveIssue, RetrospectiveReport
from .plan_chapter import normalize_book_for_plan


SYNC_LABELS = [
    "需要同步到人物弧线",
    "需要同步到信息释放表",
    "需要同步到伏笔回声表",
    "需要同步到书纲",
    "需要归档的旧案",
]


def book_retrospective_path(project: Path, *, book: str) -> Path:
    return project / "07_audits" / "book_retrospectives" / f"{book}_retrospective.md"


def extract_line_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^[ \t]*-[ \t]*{re.escape(label)}[：:][ \t]*(.*?)[ \t]*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(1).strip()
    return "" if blankish(value) else value


def extract_actual_chars(text: str) -> str:
    return extract_line_value(text, "实际字数")


def extract_sync_items(text: str) -> list[str]:
    items: list[str] = []
    for label in SYNC_LABELS:
        value = extract_line_value(text, label)
        if value:
            items.append(f"{label}: {value}")
    return items


def build_retrospective_report(project: Path, *, book: str) -> RetrospectiveReport:
    resolved = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)
    chapter_files = collect_book_files(resolved, book=book_id, kind="chapters")
    retrospectives = collect_book_files(resolved, book=book_id, kind="revision_notes")
    book_retro = book_retrospective_path(resolved, book=book_id)
    book_exists = book_retro.exists()
    book_placeholder = False
    if book_exists:
        book_placeholder = looks_placeholder(book_retro.read_text(encoding="utf-8"))

    chapters: list[RetrospectiveChapter] = []
    issues: list[RetrospectiveIssue] = []
    placeholder_count = 0
    sync_count = 0

    if not book_exists:
        issues.append(
            RetrospectiveIssue(
                severity="P3",
                code="missing_book_retrospective",
                chapter="-",
                path=display_path(book_retro, resolved),
                message="Book retrospective file is missing.",
            )
        )
    elif book_placeholder:
        issues.append(
            RetrospectiveIssue(
                severity="P4",
                code="placeholder_book_retrospective",
                chapter="-",
                path=display_path(book_retro, resolved),
                message="Book retrospective still looks like a template.",
            )
        )

    if not chapter_files:
        issues.append(
            RetrospectiveIssue(
                severity="P2",
                code="no_chapter_files",
                chapter="-",
                path=display_path(resolved / "06_drafts" / book_id / "chapters", resolved),
                message="No chapter draft files were found for this book.",
            )
        )

    for chapter_key, chapter_file in chapter_files.items():
        retrospective_file = retrospectives.get(chapter_key)
        placeholder = False
        actual_chars = ""
        sync_items: list[str] = []
        if retrospective_file is None:
            issues.append(
                RetrospectiveIssue(
                    severity="P3",
                    code="missing_chapter_retrospective",
                    chapter=chapter_key,
                    path=display_path(chapter_file, resolved),
                    message="Chapter draft exists but no matching chapter retrospective/revision note was found.",
                )
            )
        else:
            text = retrospective_file.read_text(encoding="utf-8")
            placeholder = looks_placeholder(text)
            actual_chars = extract_actual_chars(text)
            sync_items = extract_sync_items(text)
            sync_count += len(sync_items)
            if placeholder:
                placeholder_count += 1
                issues.append(
                    RetrospectiveIssue(
                        severity="P4",
                        code="placeholder_chapter_retrospective",
                        chapter=chapter_key,
                        path=display_path(retrospective_file, resolved),
                        message="Chapter retrospective still looks like a template.",
                    )
                )
            for item in sync_items:
                issues.append(
                    RetrospectiveIssue(
                        severity="P4",
                        code="open_sync_item",
                        chapter=chapter_key,
                        path=display_path(retrospective_file, resolved),
                        message=item,
                    )
                )

        chapters.append(
            RetrospectiveChapter(
                chapter=chapter_key,
                chapter_file=display_path(chapter_file, resolved),
                retrospective_file=display_path(retrospective_file, resolved) if retrospective_file else None,
                retrospective_placeholder=placeholder,
                actual_chars=actual_chars,
                sync_items=sync_items,
            )
        )

    missing = sum(1 for chapter in chapters if chapter.retrospective_file is None)
    return RetrospectiveReport(
        target=str(resolved),
        book=book_id,
        book_retrospective_file=str(book_retro),
        book_retrospective_exists=book_exists,
        book_retrospective_placeholder=book_placeholder,
        chapter_count=len(chapter_files),
        retrospective_count=len(retrospectives),
        missing_retrospectives=missing,
        placeholder_retrospectives=placeholder_count,
        sync_item_count=sync_count,
        chapters=chapters,
        issues=issues,
    )


def format_retrospective_report(report: RetrospectiveReport) -> str:
    lines = [
        "# FictionOps Retrospective",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Book retrospective: `{report.book_retrospective_file}`",
        f"- Book retrospective exists: {'yes' if report.book_retrospective_exists else 'no'}",
        f"- Book retrospective placeholder: {'yes' if report.book_retrospective_placeholder else 'no'}",
        f"- Chapters: {report.chapter_count}",
        f"- Chapter retrospectives: {report.retrospective_count}",
        f"- Missing retrospectives: {report.missing_retrospectives}",
        f"- Placeholder retrospectives: {report.placeholder_retrospectives}",
        f"- Open sync items: {report.sync_item_count}",
        f"- Issues: {len(report.issues)}",
        "",
        "## Chapter Retrospectives",
        "",
        "| Chapter | Draft | Retrospective | Placeholder | Actual Chars | Sync Items |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    if report.chapters:
        for chapter in report.chapters:
            lines.append(
                "| "
                + " | ".join(
                    [
                        chapter.chapter,
                        f"`{safe_cell(chapter.chapter_file)}`",
                        f"`{safe_cell(chapter.retrospective_file)}`" if chapter.retrospective_file else "-",
                        "yes" if chapter.retrospective_placeholder else "no",
                        safe_cell(chapter.actual_chars),
                        "<br>".join(safe_cell(item) for item in chapter.sync_items) if chapter.sync_items else "-",
                    ]
                )
                + " |"
            )
    else:
        lines.append("| - | No chapter drafts found. | - | - | - | - |")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Chapter | Path | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {issue.code} | {issue.chapter} | `{safe_cell(issue.path)}` | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No retrospective maintenance gaps found.")
    return "\n".join(lines)


def render_retrospective_report(report: RetrospectiveReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ == "markdown":
        return format_retrospective_report(report)
    raise ValueError(f"Unsupported retrospective format: {format_}")
