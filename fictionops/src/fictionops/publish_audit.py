from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .export_clean import DRAFT_MARKERS, collect_export_chapters, default_clean_output_path
from .markdown import chinese_numeral_to_int, is_cjk, safe_cell
from .models import PublishAuditChapter, PublishAuditIssue, PublishAuditReport
from .plan_chapter import normalize_book_for_plan


def resolve_publish_audit_file(target: Path, *, book: str, file_path: str | None) -> Path:
    if target.is_file():
        return target.resolve()
    if file_path:
        path = Path(file_path).expanduser()
        if path.is_absolute():
            return path.resolve()
        return (target / path).resolve()
    return default_clean_output_path(target, book=book).resolve()


def extract_heading_chapter_number(heading: str) -> int | None:
    patterns = [
        r"第\s*(\d+)\s*章",
        r"chapter\s*(\d+)",
        r"ch[_-]?(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, heading, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    chinese = re.search(r"第\s*([零〇一二三四五六七八九十百两]+)\s*章", heading)
    if chinese:
        return chinese_numeral_to_int(chinese.group(1))
    return None


def split_clean_chapters(text: str) -> list[tuple[int, str, int | None, str]]:
    headings: list[tuple[int, str, int | None]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = match.group(1).strip()
        chapter_number = extract_heading_chapter_number(heading)
        if chapter_number is not None:
            headings.append((index, heading, chapter_number))

    chapters: list[tuple[int, str, int | None, str]] = []
    for pos, (line_no, heading, chapter_number) in enumerate(headings):
        start = line_no - 1
        end = headings[pos + 1][0] - 1 if pos + 1 < len(headings) else len(lines)
        body = "\n".join(lines[start:end]).strip()
        chapters.append((line_no, heading, chapter_number, body))
    return chapters


def draft_chapter_count(project: Path, *, book: str) -> int:
    try:
        return len(collect_export_chapters(project, book=book))
    except OSError:
        return 0


def build_publish_audit_report(
    target: Path,
    *,
    book: str,
    file_path: str | None,
    min_chapter_chars: int,
) -> PublishAuditReport:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")

    book_id = normalize_book_for_plan(book)
    clean_file = resolve_publish_audit_file(resolved, book=book_id, file_path=file_path)
    project = resolved if resolved.is_dir() else resolved.parent
    drafts = draft_chapter_count(project, book=book_id) if resolved.is_dir() else 0
    issues: list[PublishAuditIssue] = []

    if not clean_file.exists():
        issues.append(
            PublishAuditIssue(
                severity="P2",
                code="missing_clean_markdown",
                chapter="-",
                line=None,
                message=f"Clean Markdown file was not found: {clean_file}",
            )
        )
        return PublishAuditReport(
            target=str(resolved),
            book=book_id,
            clean_file=str(clean_file),
            clean_file_exists=False,
            draft_chapters=drafts,
            clean_chapters=0,
            total_nonspace_chars=0,
            total_cjk_chars=0,
            issues=issues,
            chapters=[],
        )
    if not clean_file.is_file():
        raise IsADirectoryError(f"clean markdown path is not a file: {clean_file}")

    text = clean_file.read_text(encoding="utf-8")
    total_nonspace = sum(1 for char in text if not char.isspace())
    total_cjk = sum(1 for char in text if is_cjk(char))
    if not text.strip():
        issues.append(
            PublishAuditIssue(
                severity="P2",
                code="empty_clean_markdown",
                chapter="-",
                line=None,
                message="Clean Markdown file is empty.",
            )
        )

    for marker in DRAFT_MARKERS:
        marker_line = next((index for index, line in enumerate(text.splitlines(), start=1) if marker in line), None)
        if marker_line is not None:
            issues.append(
                PublishAuditIssue(
                    severity="P2",
                    code="draft_marker_left",
                    chapter="-",
                    line=marker_line,
                    message=f"Draft marker is still present: {marker}",
                )
            )
            break

    parsed = split_clean_chapters(text)
    if not parsed and text.strip():
        issues.append(
            PublishAuditIssue(
                severity="P2",
                code="no_chapter_headings",
                chapter="-",
                line=None,
                message="No recognizable chapter headings were found.",
            )
        )

    chapters: list[PublishAuditChapter] = []
    seen: dict[int, int] = {}
    previous_number: int | None = None
    numbers: list[int] = []
    for line_no, heading, chapter_number, body in parsed:
        number_label = f"{chapter_number:03d}" if chapter_number is not None else "-"
        nonspace = sum(1 for char in body if not char.isspace())
        cjk = sum(1 for char in body if is_cjk(char))
        chapter = PublishAuditChapter(
            chapter=number_label,
            heading=heading,
            line=line_no,
            chars=len(body),
            nonspace_chars=nonspace,
            cjk_chars=cjk,
            lines=body.count("\n") + (1 if body and not body.endswith("\n") else 0),
        )
        chapters.append(chapter)
        if chapter_number is None:
            continue
        numbers.append(chapter_number)
        if chapter_number in seen:
            issues.append(
                PublishAuditIssue(
                    severity="P2",
                    code="duplicate_chapter",
                    chapter=number_label,
                    line=line_no,
                    message=f"Chapter number duplicates line {seen[chapter_number]}.",
                )
            )
        else:
            seen[chapter_number] = line_no
        if previous_number is not None and chapter_number <= previous_number:
            issues.append(
                PublishAuditIssue(
                    severity="P2",
                    code="chapter_order_regression",
                    chapter=number_label,
                    line=line_no,
                    message="Chapter number is not greater than the previous chapter number.",
                )
            )
        previous_number = chapter_number
        if nonspace < min_chapter_chars:
            issues.append(
                PublishAuditIssue(
                    severity="P3",
                    code="short_chapter",
                    chapter=number_label,
                    line=line_no,
                    message=f"Chapter is below min nonspace chars: {nonspace} < {min_chapter_chars}.",
                )
            )

    if numbers:
        missing = [number for number in range(min(numbers), max(numbers) + 1) if number not in seen]
        if missing:
            issues.append(
                PublishAuditIssue(
                    severity="P3",
                    code="chapter_number_gap",
                    chapter="-",
                    line=None,
                    message="Missing chapter numbers in clean Markdown: " + ", ".join(f"{number:03d}" for number in missing),
                )
            )

    if drafts and len(chapters) != drafts:
        issues.append(
            PublishAuditIssue(
                severity="P3",
                code="draft_clean_count_mismatch",
                chapter="-",
                line=None,
                message=f"Draft chapter count and clean chapter count differ: {drafts} != {len(chapters)}.",
            )
        )

    return PublishAuditReport(
        target=str(resolved),
        book=book_id,
        clean_file=str(clean_file),
        clean_file_exists=True,
        draft_chapters=drafts,
        clean_chapters=len(chapters),
        total_nonspace_chars=total_nonspace,
        total_cjk_chars=total_cjk,
        issues=issues,
        chapters=chapters,
    )


def render_publish_audit_report(report: PublishAuditReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported audit-publish format: {format_}")

    lines = [
        "# FictionOps Publish Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Clean file: `{report.clean_file}`",
        f"- Clean file exists: {'yes' if report.clean_file_exists else 'no'}",
        f"- Draft chapters: {report.draft_chapters}",
        f"- Clean chapters: {report.clean_chapters}",
        f"- Nonspace: {report.total_nonspace_chars}",
        f"- CJK: {report.total_cjk_chars}",
        f"- Issues: {len(report.issues)}",
        "",
        "## Chapters",
        "",
        "| # | Chapter | Line | Heading | Nonspace | CJK | Lines |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    if report.chapters:
        for index, chapter in enumerate(report.chapters, start=1):
            lines.append(
                f"| {index} | {chapter.chapter} | {chapter.line} | {safe_cell(chapter.heading)} | "
                f"{chapter.nonspace_chars} | {chapter.cjk_chars} | {chapter.lines} |"
            )
    else:
        lines.append("| - | - | - | No recognizable chapters found. | - | - | - |")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Chapter | Line | Message |", "| --- | --- | --- | ---: | --- |"])
        for issue in report.issues:
            line = str(issue.line) if issue.line is not None else "-"
            lines.append(
                f"| {issue.severity} | {issue.code} | {issue.chapter} | {line} | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No publish maintenance gaps found.")
    return "\n".join(lines)
