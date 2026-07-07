from __future__ import annotations

import json
import re
import shutil
from hashlib import sha1
from dataclasses import asdict
from pathlib import Path

from .markdown import display_path, safe_cell
from .models import AdoptCopy, AdoptFile, AdoptLayerSummary, AdoptReport, AdoptRisk


ADOPT_EXTENSIONS = {".md", ".txt", ".yml", ".yaml", ".json"}
ADOPT_MANIFEST_PATH = Path("00_management") / "adopted_handoff" / "adopt_manifest.json"
DEFAULT_IGNORE_DIRS = {
    ".git",
    ".github",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "fictionops",
    "node_modules",
}

LAYER_ORDER = [
    "management",
    "story_seed",
    "world",
    "characters",
    "structure",
    "canon",
    "drafts",
    "audits",
    "publish",
    "archive",
    "unknown",
]

MIGRATION_PHASE_BY_LAYER = {
    "management": "foundation",
    "story_seed": "foundation",
    "world": "foundation",
    "characters": "foundation",
    "structure": "book-plan",
    "canon": "canon-sync",
    "drafts": "draft-import",
    "audits": "review",
    "publish": "publish",
    "archive": "archive",
    "unknown": "manual-review",
}


def should_ignore(path: Path, *, root: Path, ignore_dirs: set[str]) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in ignore_dirs for part in relative.parts)


def iter_adopt_files(root: Path, *, ignore_dirs: set[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if should_ignore(path, root=root, ignore_dirs=ignore_dirs):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in ADOPT_EXTENSIONS:
            continue
        files.append(path)
    return sorted(files, key=lambda item: display_path(item, root))


def contains_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def suggested_target_path(path: Path, *, layer: str) -> str:
    name = path.name
    lowered = name.lower()
    if layer == "management":
        if contains_any(name, ["接手", "当前"]) or "handoff" in lowered:
            return f"00_management/adopted_handoff/{name}"
        if contains_any(name, ["工作流"]) or "workflow" in lowered:
            return f"00_management/{name}"
        return f"00_management/imported/{name}"
    if layer == "story_seed":
        return f"01_story_seed/imported/{name}"
    if layer == "world":
        return f"02_world/imported/{name}"
    if layer == "characters":
        if contains_any(name, ["弧线"]) or "arc" in lowered:
            return f"03_characters/character_arcs/imported/{name}"
        if contains_any(name, ["智慧"]):
            return f"03_characters/intelligence_profiles.imported.{path.suffix.lstrip('.') or 'md'}"
        if contains_any(name, ["口吻", "voice"]):
            return f"03_characters/voice_profiles.imported.{path.suffix.lstrip('.') or 'md'}"
        return f"03_characters/imported/{name}"
    if layer == "structure":
        if contains_any(name, ["本书大纲", "分本大纲"]) or "book" in lowered:
            return f"04_structure/book_outlines/imported/{name}"
        if contains_any(name, ["卷"]):
            return f"04_structure/volume_outlines/imported/{name}"
        return f"04_structure/imported/{name}"
    if layer == "canon":
        if contains_any(name, ["信息释放"]):
            return "05_canon/information_release_table.imported.md"
        if contains_any(name, ["伏笔", "回声"]):
            return "05_canon/foreshadowing_echo_table.imported.md"
        if contains_any(name, ["时间线", "年龄"]):
            return "05_canon/timeline_and_age.imported.md"
        if contains_any(name, ["路线"]):
            return "05_canon/routes.imported.md"
        if contains_any(name, ["物件"]):
            return "05_canon/object_locations.imported.md"
        return f"05_canon/imported/{name}"
    if layer == "drafts":
        return f"06_drafts/import_queue/{name}"
    if layer == "audits":
        return f"07_audits/imported/{name}"
    if layer == "publish":
        return f"08_publish/imported/{name}"
    if layer == "archive":
        return f"99_archive/imported/{name}"
    return f"00_management/adopt_review/{name}"


def classify_file(path: Path, *, root: Path) -> tuple[str, str]:
    rel = display_path(path, root)
    lowered = rel.lower()
    name = path.name
    lowered_name = name.lower()

    if contains_any(rel, ["归档", "旧稿", "废案"]) or "archive" in lowered or "old" in lowered:
        return "archive", "archived or deprecated material"
    if contains_any(rel, ["发布包", "发布信息", "简介", "标签"]) or "publish" in lowered:
        return "publish", "publish material"
    if contains_any(rel, ["复盘", "校对", "审", "清单"]) or "audit" in lowered or "revision" in lowered:
        return "audits", "audit or revision memory"
    chapter_like = bool(re.search(r"(第\s*[\d零〇一二三四五六七八九十百两]+\s*章|ch[_-]?\d+)", name, flags=re.IGNORECASE))
    if chapter_like or "chapter" in lowered or "chapters" in lowered:
        return "drafts", "chapter draft or chapter-adjacent file"

    if contains_any(name, ["接手", "工作流", "目录说明", "统计", "当前"]) or "handoff" in lowered_name:
        return "management", "management or handoff file"
    if contains_any(name, ["信息释放", "伏笔", "回声", "时间线", "年龄", "路线", "物件"]) or "canon" in lowered_name:
        return "canon", "canon table or continuity state"
    if contains_any(name, ["人物", "角色", "弧线", "智慧", "口吻"]) or "character" in lowered_name:
        return "characters", "character memory"
    if contains_any(name, ["势力", "制度", "神话", "地理", "信仰", "命名", "世界"]) or "world" in lowered_name:
        return "world", "world or institution memory"
    if contains_any(name, ["总纲", "卷", "本书大纲", "分本大纲", "结构", "大纲", "出场"]) or "outline" in lowered_name:
        return "structure", "outline or structure file"
    if contains_any(name, ["故事种子", "故事"]) or "story_seed" in lowered_name or "seed" in lowered_name:
        return "story_seed", "story seed"

    if contains_any(rel, ["接手", "工作流", "目录说明", "统计", "当前"]) or "handoff" in lowered:
        return "management", "management or handoff file"
    if contains_any(rel, ["人物", "角色", "弧线", "智慧", "口吻"]) or "character" in lowered:
        return "characters", "character memory"
    if contains_any(rel, ["势力", "制度", "神话", "地理", "信仰", "命名", "世界"]) or "world" in lowered:
        return "world", "world or institution memory"
    if contains_any(rel, ["信息释放", "伏笔", "回声", "时间线", "年龄", "路线", "物件"]) or "canon" in lowered:
        return "canon", "canon table or continuity state"
    if contains_any(rel, ["总纲", "卷", "本书大纲", "分本大纲", "结构", "大纲"]) or "outline" in lowered:
        return "structure", "outline or structure file"
    if contains_any(rel, ["故事种子", "故事"]) or "story_seed" in lowered or "seed" in lowered:
        return "story_seed", "story seed"
    return "unknown", "unclassified project material"


def read_nonspace(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return sum(1 for char in text if not char.isspace())


def make_layer_summaries(files: list[AdoptFile]) -> list[AdoptLayerSummary]:
    summaries: list[AdoptLayerSummary] = []
    for layer in LAYER_ORDER:
        layer_files = [item for item in files if item.layer == layer]
        if not layer_files:
            continue
        summaries.append(
            AdoptLayerSummary(
                layer=layer,
                files=len(layer_files),
                nonspace_chars=sum(item.nonspace_chars for item in layer_files),
            )
        )
    return summaries


def make_risks(root: Path, files: list[AdoptFile], layer_summaries: list[AdoptLayerSummary]) -> list[AdoptRisk]:
    risks: list[AdoptRisk] = []
    layers = {summary.layer for summary in layer_summaries}
    if not (root / "project.yml").exists():
        risks.append(AdoptRisk("P2", "missing_project_config", "No FictionOps project.yml found at the target root."))
    if "drafts" in layers and "structure" not in layers:
        risks.append(AdoptRisk("P2", "drafts_without_outlines", "Chapter-like files exist, but no obvious outline layer was found."))
    if "drafts" in layers and "canon" not in layers:
        risks.append(AdoptRisk("P2", "drafts_without_canon_tables", "Chapter-like files exist, but no obvious canon/information/echo tables were found."))
    if "characters" not in layers:
        risks.append(AdoptRisk("P3", "missing_character_layer", "No obvious character memory layer was found."))
    unknown_count = sum(1 for item in files if item.layer == "unknown")
    if unknown_count:
        risks.append(AdoptRisk("P4", "unclassified_files", f"{unknown_count} file(s) could not be mapped to a FictionOps layer."))
    archived_count = sum(1 for item in files if item.layer == "archive")
    if archived_count:
        risks.append(AdoptRisk("P4", "archive_present", f"{archived_count} archived/deprecated file(s) should stay separate during migration."))
    return risks


def make_next_actions(risks: list[AdoptRisk], layer_summaries: list[AdoptLayerSummary]) -> list[str]:
    layers = {summary.layer for summary in layer_summaries}
    actions = [
        "Run `fictionops init <new-project>` in a separate directory before copying legacy material.",
        "Move or copy material by layer instead of flattening everything into one outline file.",
    ]
    if "management" in layers:
        actions.append("Promote the best handoff/current-context file into `00_management/current_context.md` and `00_management/handoff_log.md`.")
    if "structure" in layers:
        actions.append("Choose the latest series/book outlines and place old outlines under `99_archive/old_outlines/`.")
    if "canon" in layers:
        actions.append("Convert information, echo, timeline, and object files into `05_canon/` tables before drafting new chapters.")
    if "characters" in layers:
        actions.append("Split character notes into character index, intelligence profiles, voice profiles, and per-character arc files.")
    if "drafts" in layers:
        actions.append("Import chapter drafts only after book outlines and chapter engines exist, then run review gates.")
    if any(risk.code == "unclassified_files" for risk in risks):
        actions.append("Review unclassified files manually; add them to management, canon, archive, or world layers before handoff.")
    return actions


def resolve_adopt_output_path(target: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (target / candidate).resolve()


def write_adopt_report(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def resolve_adopt_copy_root(source_root: Path, copy_to: str | None) -> Path | None:
    if not copy_to:
        return None
    copy_root = Path(copy_to).expanduser().resolve()
    if not copy_root.exists():
        raise FileNotFoundError(f"copy target does not exist: {copy_root}")
    if not copy_root.is_dir():
        raise ValueError(f"copy target must be a directory: {copy_root}")
    if not (copy_root / "project.yml").exists():
        raise ValueError(f"copy target must be an initialized FictionOps project with project.yml: {copy_root}")
    try:
        copy_root.relative_to(source_root)
    except ValueError:
        pass
    else:
        raise ValueError("copy target must be outside the adopted source directory")
    return copy_root


def resolve_adopt_copy_path(copy_root: Path, suggested_target: str) -> Path:
    destination = (copy_root / suggested_target).resolve()
    try:
        destination.relative_to(copy_root)
    except ValueError as exc:
        raise ValueError(f"suggested target escapes copy target: {suggested_target}") from exc
    return destination


def safe_collision_slug(text: str) -> str:
    slug = re.sub(r'[<>:"/\\|?*\s]+', "_", text.strip())
    slug = re.sub(r"_+", "_", slug).strip("._")
    return slug or "source"


def disambiguate_copy_path(copy_root: Path, root: Path, source_path: Path, destination: Path) -> Path:
    relative_source = display_path(source_path, root)
    digest = sha1(relative_source.encode("utf-8")).hexdigest()[:8]
    context_parts = source_path.relative_to(root).with_suffix("").parts[-4:]
    context = safe_collision_slug("__".join(context_parts))
    if len(context) > 90:
        context = context[-90:].strip("._") or "source"
    candidate = destination.with_name(f"{destination.stem}.{context}.{digest}{destination.suffix}")
    try:
        candidate.relative_to(copy_root)
    except ValueError as exc:
        raise ValueError(f"disambiguated target escapes copy target: {candidate}") from exc
    return candidate


def copy_adopt_files(
    root: Path,
    copy_root: Path,
    source_files: list[Path],
    adopt_files: list[AdoptFile],
    *,
    force: bool,
    dry_run: bool,
) -> list[AdoptCopy]:
    results: list[AdoptCopy] = []
    planned_targets: set[Path] = set()
    for source_path, item in zip(source_files, adopt_files):
        destination = resolve_adopt_copy_path(copy_root, item.suggested_target_path)
        collision_disambiguated = False
        relative_destination = display_path(destination, copy_root)
        if destination in planned_targets:
            destination = disambiguate_copy_path(copy_root, root, source_path, destination)
            collision_disambiguated = True
            relative_destination = display_path(destination, copy_root)
        planned_targets.add(destination)
        if destination.exists() and not force:
            results.append(
                AdoptCopy(
                    source_path=display_path(source_path, root),
                    target_path=relative_destination,
                    status="skipped_exists",
                    message="Target exists; pass --force to overwrite.",
                )
            )
            continue
        if dry_run:
            results.append(
                AdoptCopy(
                    source_path=display_path(source_path, root),
                    target_path=relative_destination,
                    status="planned",
                    message=(
                        "Would copy source file to a unique target path because the suggested target collides."
                        if collision_disambiguated
                        else "Would copy source file to the suggested target path."
                    ),
                )
            )
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        results.append(
            AdoptCopy(
                source_path=display_path(source_path, root),
                target_path=relative_destination,
                status="copied",
                message=(
                    "Copied source file to a unique target path because the suggested target collides."
                    if collision_disambiguated
                    else "Copied source file to the suggested target path."
                ),
            )
        )
    return results


def write_adopt_manifest(copy_root: Path, root: Path, copy_files: list[AdoptCopy]) -> None:
    manifest_path = copy_root / ADOPT_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "fictionops.adopt_manifest.v1",
        "source_root": str(root),
        "copy_root": str(copy_root),
        "files": [asdict(item) for item in copy_files],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build_adopt_report(
    target: Path,
    *,
    max_files: int = 80,
    include_ignored: bool = False,
    out: str | None = None,
    copy_to: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> AdoptReport:
    root = target.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"adopt requires a directory: {root}")
    if max_files < 0:
        raise ValueError("adopt --max-files must be >= 0")

    ignore_dirs = set() if include_ignored else set(DEFAULT_IGNORE_DIRS)
    all_candidates = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in ADOPT_EXTENSIONS]
    files_to_scan = iter_adopt_files(root, ignore_dirs=ignore_dirs)
    copy_root = resolve_adopt_copy_root(root, copy_to)
    adopt_files: list[AdoptFile] = []
    for path in files_to_scan:
        layer, role = classify_file(path, root=root)
        adopt_files.append(
            AdoptFile(
                path=display_path(path, root),
                layer=layer,
                role=role,
                migration_phase=MIGRATION_PHASE_BY_LAYER.get(layer, "manual-review"),
                suggested_target_path=suggested_target_path(path, layer=layer),
                extension=path.suffix.lower(),
                bytes=path.stat().st_size,
                nonspace_chars=read_nonspace(path),
            )
        )

    layer_summaries = make_layer_summaries(adopt_files)
    risks = make_risks(root, adopt_files, layer_summaries)
    output_path = resolve_adopt_output_path(root, out) if out else None
    if output_path and output_path.exists() and not force and not dry_run:
        raise FileExistsError(output_path)
    copy_files: list[AdoptCopy] = []
    if copy_root:
        copy_files = copy_adopt_files(
            root,
            copy_root,
            files_to_scan,
            adopt_files,
            force=force,
            dry_run=dry_run,
        )
        if not dry_run:
            write_adopt_manifest(copy_root, root, copy_files)
    report = AdoptReport(
        target=str(root),
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        scanned_files=len(files_to_scan),
        included_files=min(max_files, len(adopt_files)),
        ignored_files=max(0, len(all_candidates) - len(files_to_scan)),
        total_nonspace_chars=sum(item.nonspace_chars for item in adopt_files),
        layer_summaries=layer_summaries,
        files=adopt_files[:max_files],
        risks=risks,
        next_actions=make_next_actions(risks, layer_summaries),
        copy_to=str(copy_root) if copy_root else None,
        copied_files=sum(1 for item in copy_files if item.status == "copied"),
        skipped_files=sum(1 for item in copy_files if item.status.startswith("skipped")),
        planned_copies=sum(1 for item in copy_files if item.status == "planned"),
        copy_files=copy_files[:max_files],
    )
    if output_path and not dry_run:
        write_adopt_report(output_path, render_adopt_report(report, "markdown"), force=force)
        report.written = True
    return report


def render_adopt_report(report: AdoptReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_adopt_report(report)


def format_adopt_report(report: AdoptReport) -> str:
    lines = [
        "# FictionOps Adopt Report",
        "",
        f"- Target: `{report.target}`",
        f"- Scanned files: {report.scanned_files}",
        f"- Listed files: {report.included_files}",
        f"- Ignored files: {report.ignored_files}",
        f"- Total nonspace chars: {report.total_nonspace_chars}",
        "",
        "## Layer Summary",
        "",
        "| Layer | Files | Nonspace Chars |",
        "| --- | ---: | ---: |",
    ]
    for summary in report.layer_summaries:
        lines.append(f"| {summary.layer} | {summary.files} | {summary.nonspace_chars} |")

    if report.risks:
        lines.extend(["", "## Migration Risks", ""])
        for risk in report.risks:
            lines.append(f"- {risk.severity} `{risk.code}` {risk.message}")

    if report.copy_to:
        lines.extend(
            [
                "",
                "## Copy Sandbox",
                "",
                f"- Copy target: `{report.copy_to}`",
                f"- Copied files: {report.copied_files}",
                f"- Skipped files: {report.skipped_files}",
                f"- Planned copies: {report.planned_copies}",
                "",
                "| Status | Target | Source | Message |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in report.copy_files:
            lines.append(
                f"| {item.status} | `{safe_cell(item.target_path)}` | `{safe_cell(item.source_path)}` | "
                f"{safe_cell(item.message)} |"
            )

    lines.extend(
        [
            "",
            "## Candidate Files",
            "",
            "| Layer | Phase | Role | Chars | Suggested Target | Path |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for item in report.files:
        lines.append(
            f"| {item.layer} | {item.migration_phase} | {safe_cell(item.role)} | {item.nonspace_chars} | "
            f"`{safe_cell(item.suggested_target_path)}` | `{safe_cell(item.path)}` |"
        )

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
