from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .markdown import display_path, is_cjk, natural_key
from .models import ExportCleanChapter, ExportCleanResult
from .plan_chapter import normalize_book_for_plan


DRAFT_MARKERS = {"> Draft starts here.", "Draft starts here."}


def default_clean_output_path(project: Path, *, book: str) -> Path:
    return project / "08_publish" / "clean_markdown" / f"{book}.md"


def resolve_clean_output_path(project: Path, out_path: str | None, *, book: str) -> Path:
    if not out_path:
        return default_clean_output_path(project, book=book).resolve()
    output = Path(out_path).expanduser()
    if output.is_absolute():
        return output.resolve()
    return (project / output).resolve()


def collect_export_chapters(project: Path, *, book: str) -> list[Path]:
    chapter_dir = project / "06_drafts" / book / "chapters"
    if not chapter_dir.exists():
        raise FileNotFoundError(f"chapter directory not found: {chapter_dir}")
    if not chapter_dir.is_dir():
        raise NotADirectoryError(f"chapter path is not a directory: {chapter_dir}")
    return sorted([path for path in chapter_dir.glob("*.md") if path.is_file()], key=natural_key)


def clean_chapter_markdown(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    lines = [line for line in lines if line.strip() not in DRAFT_MARKERS]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def chapter_export_stats(path: Path, text: str, *, base: Path) -> ExportCleanChapter:
    return ExportCleanChapter(
        chapter=path.stem,
        source_file=display_path(path, base),
        chars=len(text),
        nonspace_chars=sum(1 for char in text if not char.isspace()),
        cjk_chars=sum(1 for char in text if is_cjk(char)),
        lines=text.count("\n") + (1 if text and not text.endswith("\n") else 0),
    )


def render_clean_markdown(chapters: list[tuple[Path, str]], *, title: str) -> str:
    parts: list[str] = []
    clean_title = title.strip()
    if clean_title:
        parts.extend([f"# {clean_title}", ""])
    for _path, text in chapters:
        if text:
            parts.append(text)
    return "\n\n".join(parts).rstrip() + "\n"


def export_clean_markdown(
    project: Path,
    *,
    book: str,
    out: str | None,
    title: str | None,
    force: bool,
    dry_run: bool,
) -> ExportCleanResult:
    resolved = project.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"path is not a directory: {resolved}")

    book_id = normalize_book_for_plan(book)
    chapter_files = collect_export_chapters(resolved, book=book_id)
    if not chapter_files:
        raise ValueError(f"no chapter Markdown files found for {book_id}")

    output_path = resolve_clean_output_path(resolved, out, book=book_id)
    clean_title = (title or "").strip()
    rendered_chapters: list[tuple[Path, str]] = []
    chapter_stats: list[ExportCleanChapter] = []
    for path in chapter_files:
        text = clean_chapter_markdown(path.read_text(encoding="utf-8"))
        rendered_chapters.append((path, text))
        chapter_stats.append(chapter_export_stats(path, text, base=resolved))

    rendered = render_clean_markdown(rendered_chapters, title=clean_title)
    if output_path.exists() and not force and not dry_run:
        raise FileExistsError(f"output file exists: {output_path}")
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8", newline="\n")

    return ExportCleanResult(
        target=str(resolved),
        book=book_id,
        output_file=str(output_path),
        title=clean_title,
        chapter_count=len(chapter_stats),
        total_chars=len(rendered),
        total_nonspace_chars=sum(chapter.nonspace_chars for chapter in chapter_stats),
        total_cjk_chars=sum(chapter.cjk_chars for chapter in chapter_stats),
        dry_run=dry_run,
        chapters=chapter_stats,
    )


def render_export_clean_result(result: ExportCleanResult, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(result), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported export-clean format: {format_}")

    lines = [
        "# FictionOps Clean Markdown Export",
        "",
        f"- Target: `{result.target}`",
        f"- Book: `{result.book}`",
        f"- Output: `{result.output_file}`",
        f"- Title: {result.title or '-'}",
        f"- Chapters: {result.chapter_count}",
        f"- Nonspace: {result.total_nonspace_chars}",
        f"- CJK: {result.total_cjk_chars}",
        f"- Dry run: {'yes' if result.dry_run else 'no'}",
        "",
        "| # | Chapter | Source | Nonspace | CJK | Lines |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for index, chapter in enumerate(result.chapters, start=1):
        lines.append(
            f"| {index} | {chapter.chapter} | `{chapter.source_file}` | "
            f"{chapter.nonspace_chars} | {chapter.cjk_chars} | {chapter.lines} |"
        )
    return "\n".join(lines)
