from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict
from pathlib import Path

from .adopt_review import import_queue_files
from .markdown import chinese_numeral_to_int, display_path, looks_placeholder, safe_cell
from .models import ImportPlanItem, ImportPlanReport
from .new_book import normalize_book_id
from .new_chapter import chapter_paths, create_chapter


CHINESE_NUMBER = "零〇一二三四五六七八九十百两"
ADOPT_MANIFEST_PATH = Path("00_management") / "adopted_handoff" / "adopt_manifest.json"


def count_nonspace(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def first_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def normalize_inferred_number(raw: str) -> str | None:
    clean = raw.strip()
    if not clean:
        return None
    if clean.isdigit():
        return f"{int(clean):03d}"
    number = chinese_numeral_to_int(clean)
    if number is None:
        return None
    return f"{number:03d}"


def infer_chapter_from_text(value: str) -> tuple[str, str, str]:
    patterns = [
        (r"(?:^|[^A-Za-z0-9])ch[_-]?(\d{1,4})(?:[^A-Za-z0-9]|$)", "high", "chapter marker"),
        (r"chapter[_-]?(\d{1,4})", "high", "chapter marker"),
        (r"第\s*(\d{1,4})\s*[章回节]", "high", "Chinese chapter marker"),
        (rf"第\s*([{CHINESE_NUMBER}]+)\s*[章回节]", "high", "Chinese chapter marker"),
    ]
    for pattern, confidence, reason in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            chapter = normalize_inferred_number(match.group(1))
            if chapter:
                return chapter, confidence, reason

    groups = re.findall(r"\d{1,4}", value)
    if len(groups) == 1:
        chapter = normalize_inferred_number(groups[0])
        if chapter:
            return chapter, "medium", "single number"
    return "", "low", "no chapter marker"


def infer_chapter(path: Path, text: str) -> tuple[str, str, str]:
    stem_result = infer_chapter_from_text(path.stem)
    if stem_result[0]:
        return stem_result[0], stem_result[1], f"{stem_result[2]} in filename"
    heading = first_heading(text)
    heading_result = infer_chapter_from_text(heading)
    if heading_result[0]:
        return heading_result[0], heading_result[1], f"{heading_result[2]} in heading"
    return "", "low", "no chapter marker in filename or first heading"


def normalize_relpath(value: str) -> str:
    return value.replace("\\", "/")


def load_adopt_manifest_sources(project: Path) -> dict[str, str]:
    manifest_path = project / ADOPT_MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    sources: dict[str, str] = {}
    for item in data.get("files", []):
        if not isinstance(item, dict):
            continue
        target_path = str(item.get("target_path", "") or "")
        source_path = str(item.get("source_path", "") or "")
        if target_path and source_path:
            sources[normalize_relpath(target_path)] = source_path
    return sources


def infer_book(path: Path, *, project: Path, default_book: str, original_source: str | None = None) -> tuple[str, str]:
    relative = display_path(path, project)
    context = " ".join(part for part in [original_source or "", relative] if part)
    match = re.search(r"book[_-]?(\d{1,3})", context, flags=re.IGNORECASE)
    if match:
        return normalize_book_id(match.group(1)), "book marker in source path"

    match = re.search(r"第\s*(\d{1,3})\s*本", context)
    if match:
        return normalize_book_id(match.group(1)), "book marker in source path"

    match = re.search(rf"第\s*([{CHINESE_NUMBER}]+)\s*本", context)
    if match:
        number = chinese_numeral_to_int(match.group(1))
        if number is not None:
            return normalize_book_id(str(number)), "book marker in source path"

    return default_book, "fallback book"


def suggested_target(project: Path, *, book: str, chapter: str) -> Path:
    target = (project / "06_drafts" / book / "chapters" / f"ch_{chapter}.md").resolve()
    try:
        target.relative_to(project)
    except ValueError as exc:
        raise ValueError(f"import target escapes project: {target}") from exc
    return target


def resolve_import_plan_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def write_import_plan(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def next_actions_for_report(report: ImportPlanReport) -> list[str]:
    actions: list[str] = []
    if report.import_queue_files == 0:
        actions.append("No files remain in `06_drafts/import_queue/`; rerun `fictionops adopt-review .`.")
        return actions
    if report.ready_count and not report.apply:
        actions.append("Review the ready rows, then rerun with `--apply` to move only unambiguous files; add `--create-scaffolds` if companion files should be generated.")
    if report.placeholder_target_count and not report.replace_placeholder_targets:
        actions.append("If existing targets are only generated placeholders, rerun with `--apply --replace-placeholder-targets` after reviewing them.")
    if report.moved_files:
        if report.create_scaffolds:
            actions.append("Review generated chapter engines and retrospectives, then fill imported chapter intent and residue.")
        else:
            actions.append("Create or sync chapter engines and retrospectives for moved chapter files.")
    if report.needs_review_count:
        actions.append("Manually inspect low-confidence, duplicate, or existing-target rows before moving them.")
    actions.append("After sorting imports, rerun `fictionops adopt-review .` and `fictionops adopt-plan .`.")
    return actions


def build_import_plan(
    project: Path,
    *,
    book: str = "book_01",
    max_files: int = 200,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    apply: bool = False,
    create_scaffolds: bool = False,
    replace_placeholder_targets: bool = False,
) -> ImportPlanReport:
    resolved = project.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"import-plan requires a FictionOps project directory: {resolved}")
    if not (resolved / "project.yml").exists():
        raise ValueError(f"import-plan requires an initialized FictionOps project with project.yml: {resolved}")
    if max_files < 0:
        raise ValueError("import-plan --max-files must be >= 0")

    default_book = normalize_book_id(book)
    queue = import_queue_files(resolved)
    manifest_sources = load_adopt_manifest_sources(resolved)
    all_items: list[ImportPlanItem] = []
    for source in queue:
        text = source.read_text(encoding="utf-8")
        relative_source = display_path(source, resolved)
        original_source = manifest_sources.get(normalize_relpath(relative_source))
        inferred_book, book_reason = infer_book(source, project=resolved, default_book=default_book, original_source=original_source)
        chapter, confidence, chapter_reason = infer_chapter(source, text)
        title = first_heading(text)
        if chapter:
            target = suggested_target(resolved, book=inferred_book, chapter=chapter)
            target_path = display_path(target, resolved)
            if target.exists():
                target_text = target.read_text(encoding="utf-8")
                status = "placeholder_target" if looks_placeholder(target_text) else "target_exists"
            else:
                status = "ready"
        else:
            target_path = "-"
            status = "needs_chapter"
        reason = f"{chapter_reason}; {book_reason}"
        all_items.append(
            ImportPlanItem(
                source_path=display_path(source, resolved),
                inferred_book=inferred_book,
                inferred_chapter=chapter or "-",
                title=title or "-",
                target_path=target_path,
                status=status,
                scaffold_status="-",
                confidence=confidence,
                reason=reason,
                nonspace_chars=count_nonspace(text),
            )
        )

    target_counts: dict[str, int] = {}
    for item in all_items:
        if item.status == "ready":
            target_counts[item.target_path] = target_counts.get(item.target_path, 0) + 1
    for item in all_items:
        if item.status == "ready" and target_counts.get(item.target_path, 0) > 1:
            item.status = "duplicate_target"

    moved_files = 0
    replaced_placeholder_targets = 0
    scaffold_created_files = 0
    scaffold_skipped_files = 0
    scaffold_planned_actions = 0
    if apply:
        for item in all_items:
            if item.status == "ready":
                replace_target = False
            elif item.status == "placeholder_target" and replace_placeholder_targets:
                replace_target = True
            else:
                continue
            source = (resolved / item.source_path).resolve()
            target = (resolved / item.target_path).resolve()
            if dry_run:
                item.status = "planned_replace_placeholder" if replace_target else "planned_move"
                if create_scaffolds and item.inferred_chapter != "-":
                    paths = chapter_paths(resolved, book=item.inferred_book, chapter_number=item.inferred_chapter)
                    planned = sum(1 for key in ["engine", "retrospective"] if not paths[key].exists())
                    scaffold_planned_actions += planned
                    item.scaffold_status = f"planned:{planned}" if planned else "exists"
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if replace_target and target.exists():
                target.unlink()
            shutil.move(str(source), str(target))
            item.status = "replaced_placeholder_target" if replace_target else "moved"
            moved_files += 1
            if replace_target:
                replaced_placeholder_targets += 1
            if create_scaffolds and item.inferred_chapter != "-":
                result = create_chapter(
                    resolved,
                    book=item.inferred_book,
                    chapter=item.inferred_chapter,
                    title=None if item.title == "-" else item.title,
                    viewpoint=None,
                    kind="imported draft",
                    target_chars=None,
                    force=False,
                    dry_run=False,
                )
                scaffold_created_files += result.created_files
                scaffold_skipped_files += result.skipped_files
                item.scaffold_status = f"created:{result.created_files}, skipped:{result.skipped_files}"

    displayed = all_items[:max_files] if max_files else []
    output_path = resolve_import_plan_output_path(resolved, out) if out else None
    report = ImportPlanReport(
        target=str(resolved),
        book=default_book,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        apply=apply,
        create_scaffolds=create_scaffolds,
        replace_placeholder_targets=replace_placeholder_targets,
        written=False,
        import_queue_files=len(queue),
        displayed_items=len(displayed),
        omitted_items=max(0, len(all_items) - len(displayed)),
        ready_count=sum(1 for item in all_items if item.status == "ready"),
        moved_files=moved_files,
        replaced_placeholder_targets=replaced_placeholder_targets,
        scaffold_created_files=scaffold_created_files,
        scaffold_skipped_files=scaffold_skipped_files,
        scaffold_planned_actions=scaffold_planned_actions,
        needs_review_count=sum(1 for item in all_items if item.status in {"needs_chapter", "duplicate_target", "target_exists", "placeholder_target"}),
        target_exists_count=sum(1 for item in all_items if item.status == "target_exists"),
        placeholder_target_count=sum(1 for item in all_items if item.status == "placeholder_target"),
        duplicate_target_count=sum(1 for item in all_items if item.status == "duplicate_target"),
        items=displayed,
        next_actions=[],
    )
    report.next_actions = next_actions_for_report(report)
    if output_path and not dry_run:
        write_import_plan(output_path, render_import_plan(report, "markdown"), force=force)
        report.written = True
    return report


def format_import_plan(report: ImportPlanReport) -> str:
    lines = [
        "# FictionOps Import Plan",
        "",
        f"- Target: `{report.target}`",
        f"- Fallback book: `{report.book}`",
        f"- Import queue files: {report.import_queue_files}",
        f"- Ready: {report.ready_count}",
        f"- Moved: {report.moved_files}",
        f"- Replace placeholder targets: {'yes' if report.replace_placeholder_targets else 'no'}",
        f"- Replaced placeholder targets: {report.replaced_placeholder_targets}",
        f"- Create scaffolds: {'yes' if report.create_scaffolds else 'no'}",
        f"- Scaffold created files: {report.scaffold_created_files}",
        f"- Scaffold skipped files: {report.scaffold_skipped_files}",
        f"- Scaffold planned actions: {report.scaffold_planned_actions}",
        f"- Needs review: {report.needs_review_count}",
        f"- Existing targets: {report.target_exists_count}",
        f"- Placeholder targets: {report.placeholder_target_count}",
        f"- Duplicate targets: {report.duplicate_target_count}",
        "",
        "## Rule",
        "",
        "This report only moves files when `--apply` is passed, and even then it moves only unambiguous rows with a missing target file. Companion chapter files are generated only when `--create-scaffolds` is also passed.",
        "",
        "## Items",
        "",
    ]
    if not report.items:
        lines.append("No import queue files found.")
    else:
        lines.extend(
            [
                "| Source | Status | Scaffold | Confidence | Book | Chapter | Target | Title | Reason | Chars |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |",
            ]
        )
        for item in report.items:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{safe_cell(item.source_path)}`",
                        safe_cell(item.status),
                        safe_cell(item.scaffold_status),
                        safe_cell(item.confidence),
                        f"`{safe_cell(item.inferred_book)}`",
                        safe_cell(item.inferred_chapter),
                        f"`{safe_cell(item.target_path)}`",
                        safe_cell(item.title),
                        safe_cell(item.reason),
                        str(item.nonspace_chars),
                    ]
                )
                + " |"
            )
        if report.omitted_items:
            lines.append(f"| - | omitted | - | - | - | - | - | - | {report.omitted_items} item(s) omitted by --max-files. | 0 |")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_import_plan(report: ImportPlanReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_import_plan(report)
