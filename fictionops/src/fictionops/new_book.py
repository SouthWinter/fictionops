from __future__ import annotations

import re
from pathlib import Path

from .init_project import template_root
from .models import NewBookResult


def normalize_book_id(book: str) -> str:
    raw = book.strip()
    patterns = [
        r"^book[_-]?(\d+)$",
        r"^(\d+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, raw, flags=re.IGNORECASE)
        if match:
            return f"book_{int(match.group(1)):02d}"
    raise ValueError(f"book must be numeric, book_01, or book-01 style: {book}")


def book_paths(project: Path, *, book: str) -> dict[str, Path]:
    return {
        "outline": project / "04_structure" / "book_outlines" / f"{book}_outline.md",
        "retrospective": project / "07_audits" / "book_retrospectives" / f"{book}_retrospective.md",
        "chapters": project / "06_drafts" / book / "chapters",
        "chapter_engines": project / "06_drafts" / book / "chapter_engines",
        "draft_briefs": project / "06_drafts" / book / "draft_briefs",
        "revision_notes": project / "06_drafts" / book / "revision_notes",
    }


def fill_line(text: str, marker: str, value: str | None) -> str:
    clean = (value or "").strip()
    if not clean:
        return text
    return text.replace(marker, f"{marker}{clean}", 1)


def render_book_outline(text: str, *, book: str, title: str | None) -> str:
    display = (title or "").strip() or book
    return text.replace("# 本书大纲模板", f"# {display} 大纲", 1)


def render_book_retrospective(text: str, *, book: str, title: str | None) -> str:
    text = fill_line(text, "- 书名：", book)
    text = fill_line(text, "- 标题：", title)
    return text


def write_book_file(path: Path, text: str, *, force: bool, dry_run: bool, result: NewBookResult) -> None:
    result.paths.append(str(path))
    if dry_run:
        result.planned_actions += 1
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        result.skipped_files += 1
        return
    path.write_text(text, encoding="utf-8", newline="\n")
    result.created_files += 1


def create_book(
    project: Path,
    *,
    book: str,
    title: str | None,
    force: bool,
    dry_run: bool,
) -> NewBookResult:
    result = NewBookResult()
    book_id = normalize_book_id(book)
    paths = book_paths(project, book=book_id)
    directories = [paths["chapters"], paths["chapter_engines"], paths["draft_briefs"], paths["revision_notes"]]

    if dry_run:
        result.planned_actions += len(directories)
        for directory in directories:
            result.paths.append(str(directory))
    else:
        for directory in directories:
            if not directory.exists():
                result.created_dirs += 1
            directory.mkdir(parents=True, exist_ok=True)

    templates = template_root()
    outline_template = templates / "book_outline.zh-CN.md"
    retrospective_template = templates / "book_retrospective.zh-CN.md"
    if not outline_template.exists():
        raise FileNotFoundError(f"Template file not found: {outline_template}")
    if not retrospective_template.exists():
        raise FileNotFoundError(f"Template file not found: {retrospective_template}")

    files = {
        paths["outline"]: render_book_outline(
            outline_template.read_text(encoding="utf-8"),
            book=book_id,
            title=title,
        ),
        paths["retrospective"]: render_book_retrospective(
            retrospective_template.read_text(encoding="utf-8"),
            book=book_id,
            title=title,
        ),
    }
    for path, text in files.items():
        write_book_file(path, text, force=force, dry_run=dry_run, result=result)
    return result
