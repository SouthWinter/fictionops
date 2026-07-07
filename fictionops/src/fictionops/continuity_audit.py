from __future__ import annotations

import re
from pathlib import Path

from .constants import STANDARD_PROJECT_FILES
from .markdown import collect_markdown_files, display_path, extract_chapter_key, looks_placeholder, natural_key, safe_cell
from .models import ChapterContinuity, ContinuityIssue, ContinuityReport, FileCheck

def chapter_key_markers(key: str) -> list[str]:
    markers = [key, f"ch_{key}", f"ch-{key}", f"ch{key}"]
    if key.isdigit():
        number = int(key)
        markers.extend(
            [
                f"ch_{number}",
                f"ch-{number}",
                f"第{number}章",
                f"第{number:02d}章",
                f"| {number} ",
                f"| {number:02d} ",
                f"| {number:03d} ",
            ]
        )
    return markers


def find_companion_file(files: list[Path], *, key: str, kind: str) -> Path | None:
    key_patterns = chapter_key_markers(key)
    scored: list[tuple[int, Path]] = []
    for path in files:
        lower_path = str(path).lower()
        stem = path.stem.lower()
        score = 0
        if kind == "engine":
            if "chapter_engine" in lower_path or "chapter_engines" in lower_path:
                score += 4
            if "engine" in stem or "发动机" in stem:
                score += 3
        elif kind == "retrospective":
            if "retrospective" in lower_path or "book_retrospectives" in lower_path or "revision_notes" in lower_path:
                score += 4
            if "retro" in stem or "retrospective" in stem or "复盘" in stem or "revision" in stem:
                score += 3
        if not score:
            continue
        has_key = any(pattern in stem or pattern in lower_path for pattern in key_patterns)
        if not has_key:
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                text = ""
            has_key = any(pattern in text for pattern in key_patterns)
        if not has_key:
            continue
        if score:
            scored.append((score, path))
    if not scored:
        return None
    return sorted(scored, key=lambda item: (-item[0], natural_key(item[1])))[0][1]


def build_continuity_report(
    target: Path,
    *,
    pattern: str,
    skip_standard: bool,
    min_chapter_chars: int,
) -> ContinuityReport:
    resolved = target.expanduser().resolve()
    base = resolved if resolved.is_dir() else resolved.parent
    all_files = collect_markdown_files(resolved, all_markdown=True, pattern=pattern)
    chapter_files = collect_markdown_files(resolved, all_markdown=False, pattern=pattern)

    standard_checks: list[FileCheck] = []
    issues: list[ContinuityIssue] = []
    if not skip_standard and resolved.is_dir():
        for relative, kind in STANDARD_PROJECT_FILES:
            path = resolved / relative
            exists = path.exists()
            placeholder = False
            if exists and path.is_file():
                placeholder = looks_placeholder(path.read_text(encoding="utf-8"))
            standard_checks.append(FileCheck(path=relative, kind=kind, exists=exists, placeholder=placeholder))
            if not exists:
                severity = "P1" if kind == "required" else "P3"
                issues.append(
                    ContinuityIssue(
                        severity=severity,
                        code="missing_standard_file",
                        path=relative,
                        message=f"{kind} project memory file is missing.",
                    )
                )
            elif placeholder:
                issues.append(
                    ContinuityIssue(
                        severity="P4",
                        code="placeholder_standard_file",
                        path=relative,
                        message="Project memory file still looks like an unfilled template.",
                    )
                )

    chapters: list[ChapterContinuity] = []
    for chapter in chapter_files:
        key = extract_chapter_key(chapter)
        chapter_text = chapter.read_text(encoding="utf-8")
        chapter_placeholder = looks_placeholder(chapter_text, min_chars=min_chapter_chars)
        engine = find_companion_file(all_files, key=key, kind="engine")
        retrospective = find_companion_file(all_files, key=key, kind="retrospective")
        engine_placeholder = False
        retrospective_placeholder = False
        if engine is not None:
            engine_placeholder = looks_placeholder(engine.read_text(encoding="utf-8"))
        if retrospective is not None:
            retrospective_placeholder = looks_placeholder(retrospective.read_text(encoding="utf-8"))

        chapter_display = display_path(chapter, base)
        chapters.append(
            ChapterContinuity(
                key=key,
                chapter_file=chapter_display,
                placeholder=chapter_placeholder,
                engine_file=display_path(engine, base) if engine else None,
                engine_placeholder=engine_placeholder,
                retrospective_file=display_path(retrospective, base) if retrospective else None,
                retrospective_placeholder=retrospective_placeholder,
            )
        )
        if chapter_placeholder:
            issues.append(
                ContinuityIssue(
                    severity="P3",
                    code="placeholder_chapter",
                    path=chapter_display,
                    message="Chapter file looks like a placeholder or is very short.",
                )
            )
        if engine is None:
            issues.append(
                ContinuityIssue(
                    severity="P2",
                    code="missing_chapter_engine",
                    path=chapter_display,
                    message="Chapter exists but no matching chapter engine was found.",
                )
            )
        elif engine_placeholder:
            issues.append(
                ContinuityIssue(
                    severity="P3",
                    code="placeholder_chapter_engine",
                    path=display_path(engine, base),
                    message="Matching chapter engine still looks like a template.",
                )
            )
        if retrospective is None:
            issues.append(
                ContinuityIssue(
                    severity="P3",
                    code="missing_chapter_retrospective",
                    path=chapter_display,
                    message="Chapter exists but no matching retrospective/revision note was found.",
                )
            )
        elif retrospective_placeholder:
            issues.append(
                ContinuityIssue(
                    severity="P4",
                    code="placeholder_retrospective",
                    path=display_path(retrospective, base),
                    message="Matching retrospective still looks like a template.",
                )
            )

    missing_standard = sum(1 for check in standard_checks if not check.exists)
    placeholder_standard = sum(1 for check in standard_checks if check.placeholder)
    missing_engine = sum(1 for chapter in chapters if chapter.engine_file is None)
    missing_retrospective = sum(1 for chapter in chapters if chapter.retrospective_file is None)
    placeholder_chapters = sum(1 for chapter in chapters if chapter.placeholder)
    return ContinuityReport(
        target=str(resolved),
        file_count=len(all_files),
        chapter_count=len(chapters),
        placeholder_chapters=placeholder_chapters,
        missing_engine_count=missing_engine,
        missing_retrospective_count=missing_retrospective,
        missing_standard_files=missing_standard,
        placeholder_standard_files=placeholder_standard,
        standard_files=standard_checks,
        chapters=chapters,
        issues=issues,
    )


def format_bool(value: bool) -> str:
    return "yes" if value else "no"


def format_continuity_report(report: ContinuityReport) -> str:
    lines = [
        "# FictionOps Continuity Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Markdown files: {report.file_count}",
        f"- Chapters: {report.chapter_count}",
        f"- Placeholder chapters: {report.placeholder_chapters}",
        f"- Missing engines: {report.missing_engine_count}",
        f"- Missing retrospectives: {report.missing_retrospective_count}",
        f"- Missing standard files: {report.missing_standard_files}",
        f"- Placeholder standard files: {report.placeholder_standard_files}",
        f"- Issues: {len(report.issues)}",
        "",
    ]
    if report.standard_files:
        lines.extend(
            [
                "## Standard Project Files",
                "",
                "| File | Kind | Exists | Placeholder |",
                "| --- | --- | --- | --- |",
            ]
        )
        for check in report.standard_files:
            lines.append(
                f"| `{check.path}` | {check.kind} | {format_bool(check.exists)} | {format_bool(check.placeholder)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Chapter Coverage",
            "",
            "| Key | Chapter | Placeholder | Engine | Engine Placeholder | Retrospective | Retrospective Placeholder |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if report.chapters:
        for chapter in report.chapters:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(chapter.key),
                        f"`{safe_cell(chapter.chapter_file)}`",
                        format_bool(chapter.placeholder),
                        f"`{safe_cell(chapter.engine_file)}`" if chapter.engine_file else "-",
                        format_bool(chapter.engine_placeholder),
                        f"`{safe_cell(chapter.retrospective_file)}`" if chapter.retrospective_file else "-",
                        format_bool(chapter.retrospective_placeholder),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| - | No chapter files found. | - | - | - | - | - |")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {issue.code} | `{safe_cell(issue.path)}` | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No continuity maintenance gaps found.")
    return "\n".join(lines)
