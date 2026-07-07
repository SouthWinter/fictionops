from __future__ import annotations

from pathlib import Path

from .constants import PROJECT_DIRS, STARTER_FILES, TEMPLATE_COPIES
from .models import InitResult


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def template_root() -> Path:
    packaged_templates = Path(__file__).resolve().parent / "templates"
    if packaged_templates.exists():
        return packaged_templates
    return project_root() / "templates"


def render_text(text: str, *, title: str, language: str) -> str:
    safe_title = title.replace('"', '\\"')
    safe_language = language.replace('"', '\\"')
    text = text.replace("{title}", title)
    text = text.replace('title: "Untitled Novel"', f'title: "{safe_title}"')
    text = text.replace('language: "zh-CN"', f'language: "{safe_language}"')
    return text


def write_file(path: Path, text: str, *, force: bool, dry_run: bool, result: InitResult) -> None:
    if dry_run:
        result.planned_actions += 1
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        result.skipped_files += 1
        return
    path.write_text(text, encoding="utf-8", newline="\n")
    result.created_files += 1


def create_project(target: Path, *, title: str, language: str, force: bool, dry_run: bool) -> InitResult:
    result = InitResult()
    templates = template_root()
    if not templates.exists():
        raise FileNotFoundError(f"Template directory not found: {templates}")

    if dry_run:
        result.planned_actions += len(PROJECT_DIRS)
    else:
        target.mkdir(parents=True, exist_ok=True)
        for rel_dir in PROJECT_DIRS:
            directory = target / rel_dir
            if not directory.exists():
                result.created_dirs += 1
            directory.mkdir(parents=True, exist_ok=True)

    for template_name, destination in TEMPLATE_COPIES.items():
        source = templates / template_name
        if not source.exists():
            raise FileNotFoundError(f"Template file not found: {source}")
        text = render_text(source.read_text(encoding="utf-8"), title=title, language=language)
        write_file(target / destination, text, force=force, dry_run=dry_run, result=result)

    for destination, text in STARTER_FILES.items():
        rendered = render_text(text, title=title, language=language)
        write_file(target / destination, rendered, force=force, dry_run=dry_run, result=result)

    return result
