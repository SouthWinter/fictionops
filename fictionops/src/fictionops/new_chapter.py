from __future__ import annotations

import re
from pathlib import Path

from .init_project import template_root
from .models import NewChapterResult


def normalize_chapter_number(chapter: str) -> str:
    raw = chapter.strip()
    patterns = [
        r"^ch[_-]?(\d+)$",
        r"^第\s*(\d+)\s*章$",
        r"^(\d+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, raw, flags=re.IGNORECASE)
        if match:
            return f"{int(match.group(1)):03d}"
    raise ValueError(f"chapter must be numeric, ch_001, or 第1章 style: {chapter}")


def chapter_heading(chapter_number: str, title: str | None) -> str:
    label = f"第{chapter_number}章"
    clean_title = (title or "").strip()
    if clean_title:
        return f"{label} {clean_title}"
    return label


def chapter_paths(project: Path, *, book: str, chapter_number: str) -> dict[str, Path]:
    book_root = project / "06_drafts" / book
    return {
        "chapter": book_root / "chapters" / f"ch_{chapter_number}.md",
        "engine": book_root / "chapter_engines" / f"ch_{chapter_number}_engine.md",
        "retrospective": book_root / "revision_notes" / f"ch_{chapter_number}_retrospective.md",
    }


def render_chapter_draft(*, chapter_number: str, title: str | None) -> str:
    heading = chapter_heading(chapter_number, title)
    return f"# {heading}\n\n> Draft starts here.\n"


def fill_line(text: str, marker: str, value: str | None) -> str:
    clean = (value or "").strip()
    if not clean:
        return text
    return text.replace(marker, f"{marker}{clean}", 1)


def render_engine_template(
    text: str,
    *,
    book: str,
    chapter_number: str,
    title: str | None,
    viewpoint: str | None,
    kind: str | None,
    target_chars: int | None,
) -> str:
    text = fill_line(text, "- 书名：", book)
    text = fill_line(text, "- 章节：", f"第{chapter_number}章")
    text = fill_line(text, "- 标题：", title)
    text = fill_line(text, "- 视角人物：", viewpoint)
    text = fill_line(text, "- 建议体量：", str(target_chars) if target_chars else None)
    clean_kind = (kind or "").strip()
    if clean_kind:
        text = text.replace("- 章节性质：", f"- 章节性质：{clean_kind} / ", 1)
    return text


def render_retrospective_template(
    text: str,
    *,
    book: str,
    chapter_number: str,
    title: str | None,
) -> str:
    text = fill_line(text, "- 书名：", book)
    text = fill_line(text, "- 章节：", f"第{chapter_number}章")
    text = fill_line(text, "- 标题：", title)
    return text


def write_chapter_file(path: Path, text: str, *, force: bool, dry_run: bool, result: NewChapterResult) -> None:
    result.paths.append(str(path))
    if dry_run:
        result.planned_actions += 1
        return
    if path.exists() and not force:
        result.skipped_files += 1
        return
    path.write_text(text, encoding="utf-8", newline="\n")
    result.created_files += 1


def create_chapter(
    project: Path,
    *,
    book: str,
    chapter: str,
    title: str | None,
    viewpoint: str | None,
    kind: str | None,
    target_chars: int | None,
    force: bool,
    dry_run: bool,
) -> NewChapterResult:
    result = NewChapterResult()
    chapter_number = normalize_chapter_number(chapter)
    paths = chapter_paths(project, book=book, chapter_number=chapter_number)

    if dry_run:
        result.planned_actions += len({path.parent for path in paths.values()})
    else:
        for directory in {path.parent for path in paths.values()}:
            if not directory.exists():
                result.created_dirs += 1
            directory.mkdir(parents=True, exist_ok=True)

    templates = template_root()
    engine_template = templates / "chapter_engine.zh-CN.md"
    retrospective_template = templates / "chapter_retrospective.zh-CN.md"
    if not engine_template.exists():
        raise FileNotFoundError(f"Template file not found: {engine_template}")
    if not retrospective_template.exists():
        raise FileNotFoundError(f"Template file not found: {retrospective_template}")

    files = {
        paths["chapter"]: render_chapter_draft(chapter_number=chapter_number, title=title),
        paths["engine"]: render_engine_template(
            engine_template.read_text(encoding="utf-8"),
            book=book,
            chapter_number=chapter_number,
            title=title,
            viewpoint=viewpoint,
            kind=kind,
            target_chars=target_chars,
        ),
        paths["retrospective"]: render_retrospective_template(
            retrospective_template.read_text(encoding="utf-8"),
            book=book,
            chapter_number=chapter_number,
            title=title,
        ),
    }
    for path, text in files.items():
        write_chapter_file(path, text, force=force, dry_run=dry_run, result=result)
    return result
