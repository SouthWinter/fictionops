from __future__ import annotations

import json
import zipfile
from dataclasses import asdict
from pathlib import Path

from .export_clean import default_clean_output_path
from .markdown import safe_cell
from .models import EpubAuditIssue, EpubAuditReport
from .plan_chapter import normalize_book_for_plan
from .publish_epub import default_epub_output_path
from .publish_manifest import default_manifest_output_path, resolve_manifest_file
from .publish_metadata import default_metadata_output_path


def epub_audit_issue(severity: str, code: str, path: Path | str, message: str) -> EpubAuditIssue:
    return EpubAuditIssue(severity=severity, code=code, path=str(path), message=message)


def project_root_for_epub_target(target: Path) -> Path:
    if target.is_file() and target.parent.name == "epub" and target.parent.parent.name == "08_publish":
        return target.parent.parent.parent.resolve()
    return (target if target.is_dir() else target.parent).resolve()


def resolve_epub_audit_file(target: Path, *, book: str, file_path: str | None) -> Path:
    project = project_root_for_epub_target(target)
    if target.is_file() and not file_path:
        return target.resolve()
    return resolve_manifest_file(project, file_path, default_path=default_epub_output_path(project, book=book))


def load_json_payload(path: Path) -> dict[str, object]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def manifest_file_path(manifest: dict[str, object], key: str) -> str | None:
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        return None
    item = files.get(key, {})
    if not isinstance(item, dict):
        return None
    path = item.get("path")
    return str(path).strip() if path else None


def metadata_cover_path(metadata_payload: dict[str, object]) -> str | None:
    metadata = metadata_payload.get("metadata", {})
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("cover_image", "")
    if isinstance(value, list):
        value = next((str(item).strip() for item in value if str(item).strip()), "")
    text = str(value).strip()
    return text or None


def resolve_audit_inputs(
    project: Path,
    *,
    book: str,
    manifest_file: str | None,
    clean_file: str | None,
    metadata_file: str | None,
) -> tuple[Path, Path, Path, Path | None]:
    manifest_path = resolve_manifest_file(
        project,
        manifest_file,
        default_path=default_manifest_output_path(project, book=book),
    )
    manifest = load_json_payload(manifest_path)
    clean_text = clean_file or manifest_file_path(manifest, "clean_markdown")
    metadata_text = metadata_file or manifest_file_path(manifest, "metadata_json")
    clean_path = resolve_manifest_file(
        project,
        clean_text,
        default_path=default_clean_output_path(project, book=book),
    )
    metadata_path = resolve_manifest_file(
        project,
        metadata_text,
        default_path=default_metadata_output_path(project, book=book),
    )
    metadata_payload = load_json_payload(metadata_path)
    cover_text = manifest_file_path(manifest, "cover_image") or metadata_cover_path(metadata_payload)
    cover_path = resolve_manifest_file(project, cover_text, default_path=Path(cover_text)) if cover_text else None
    return manifest_path, clean_path, metadata_path, cover_path


def output_older_than_inputs(output_file: Path, input_files: list[Path]) -> bool:
    if not output_file.exists() or not output_file.is_file():
        return False
    try:
        output_mtime = output_file.stat().st_mtime
    except OSError:
        return False
    for input_file in input_files:
        try:
            if input_file.exists() and input_file.stat().st_mtime > output_mtime:
                return True
        except OSError:
            continue
    return False


def build_epub_audit_report(
    target: Path,
    *,
    book: str,
    file_path: str | None,
    manifest_file: str | None,
    clean_file: str | None,
    metadata_file: str | None,
) -> EpubAuditReport:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")

    book_id = normalize_book_for_plan(book)
    project = project_root_for_epub_target(resolved)
    epub_path = resolve_epub_audit_file(resolved, book=book_id, file_path=file_path)
    manifest_path, clean_path, metadata_path, cover_path = resolve_audit_inputs(
        project,
        book=book_id,
        manifest_file=manifest_file,
        clean_file=clean_file,
        metadata_file=metadata_file,
    )

    issues: list[EpubAuditIssue] = []
    exists = epub_path.exists() and epub_path.is_file()
    mimetype_first = False
    mimetype_valid = False
    has_container = False
    has_opf = False
    has_nav = False
    has_css = False
    chapter_count = 0
    has_cover_page = False
    has_cover_image = False
    opf_cover_declared = False

    if resolved.is_dir() and not manifest_path.exists():
        issues.append(
            epub_audit_issue(
                "P3",
                "missing_manifest",
                manifest_path,
                "Publish manifest was not found; freshness and cover checks may be incomplete.",
            )
        )

    if not exists:
        issues.append(epub_audit_issue("P3", "missing_epub", epub_path, "EPUB file was not found."))
    else:
        try:
            with zipfile.ZipFile(epub_path, "r") as zf:
                names = zf.namelist()
                mimetype_first = bool(names) and names[0] == "mimetype"
                if not mimetype_first:
                    issues.append(
                        epub_audit_issue(
                            "P2",
                            "mimetype_not_first",
                            epub_path,
                            "EPUB mimetype entry must be the first archive item.",
                        )
                    )
                try:
                    mimetype_valid = zf.read("mimetype").decode("utf-8") == "application/epub+zip"
                except (KeyError, UnicodeDecodeError):
                    mimetype_valid = False
                if not mimetype_valid:
                    issues.append(epub_audit_issue("P2", "invalid_mimetype", epub_path, "EPUB mimetype entry is missing or invalid."))

                has_container = "META-INF/container.xml" in names
                has_opf = "OEBPS/content.opf" in names
                has_nav = "OEBPS/nav.xhtml" in names
                has_css = "OEBPS/styles/fictionops.css" in names
                chapter_count = len([item for item in names if item.startswith("OEBPS/chapters/") and item.endswith(".xhtml")])
                has_cover_page = "OEBPS/cover.xhtml" in names
                has_cover_image = any(item.startswith("OEBPS/images/cover.") for item in names)

                required = [
                    ("missing_container", has_container, "META-INF/container.xml"),
                    ("missing_opf", has_opf, "OEBPS/content.opf"),
                    ("missing_nav", has_nav, "OEBPS/nav.xhtml"),
                    ("missing_css", has_css, "OEBPS/styles/fictionops.css"),
                ]
                for code, present, name in required:
                    if not present:
                        issues.append(epub_audit_issue("P2", code, epub_path, f"EPUB is missing required file: {name}."))
                if chapter_count == 0:
                    issues.append(epub_audit_issue("P2", "missing_chapters", epub_path, "EPUB contains no chapter XHTML files."))

                if has_opf:
                    try:
                        opf_text = zf.read("OEBPS/content.opf").decode("utf-8")
                    except (KeyError, UnicodeDecodeError):
                        opf_text = ""
                    opf_cover_declared = "cover-image" in opf_text
                    if opf_cover_declared and not (has_cover_page and has_cover_image):
                        issues.append(
                            epub_audit_issue(
                                "P2",
                                "broken_cover_manifest",
                                epub_path,
                                "OPF declares a cover image, but the cover page or image is missing.",
                            )
                        )
        except (OSError, zipfile.BadZipFile) as exc:
            issues.append(epub_audit_issue("P2", "invalid_epub_archive", epub_path, f"EPUB archive could not be opened: {exc}"))

    if cover_path and cover_path.exists() and exists and not (has_cover_page and has_cover_image):
        issues.append(
            epub_audit_issue(
                "P3",
                "cover_not_packaged",
                epub_path,
                "A cover image is recorded in metadata or manifest, but the EPUB does not package it.",
            )
        )

    input_files = [manifest_path, clean_path, metadata_path]
    if cover_path:
        input_files.append(cover_path)
    stale = output_older_than_inputs(epub_path, input_files)
    if stale:
        issues.append(
            epub_audit_issue(
                "P3",
                "stale_epub",
                epub_path,
                "EPUB is older than the current clean Markdown, metadata JSON, manifest, or cover image.",
            )
        )

    valid = exists and not any(issue.severity in {"P1", "P2"} for issue in issues)
    return EpubAuditReport(
        target=str(resolved),
        book=book_id,
        epub_file=str(epub_path),
        manifest_file=str(manifest_path),
        clean_file=str(clean_path),
        metadata_file=str(metadata_path),
        cover_file=str(cover_path) if cover_path else "",
        epub_file_exists=exists,
        epub_valid=valid,
        stale=stale,
        mimetype_first=mimetype_first,
        mimetype_valid=mimetype_valid,
        has_container=has_container,
        has_opf=has_opf,
        has_nav=has_nav,
        has_css=has_css,
        chapter_count=chapter_count,
        has_cover_page=has_cover_page,
        has_cover_image=has_cover_image,
        opf_cover_declared=opf_cover_declared,
        issues=issues,
    )


def render_epub_audit_report(report: EpubAuditReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported audit-epub format: {format_}")

    lines = [
        "# FictionOps EPUB Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- EPUB: `{report.epub_file}`",
        f"- EPUB exists: {'yes' if report.epub_file_exists else 'no'}",
        f"- EPUB valid: {'yes' if report.epub_valid else 'no'}",
        f"- Stale: {'yes' if report.stale else 'no'}",
        f"- Manifest: `{report.manifest_file}`",
        f"- Clean Markdown: `{report.clean_file}`",
        f"- Metadata JSON: `{report.metadata_file}`",
        f"- Cover image: `{report.cover_file or '-'}`",
        "",
        "## Structure",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| mimetype first | {'yes' if report.mimetype_first else 'no'} |",
        f"| mimetype valid | {'yes' if report.mimetype_valid else 'no'} |",
        f"| container | {'yes' if report.has_container else 'no'} |",
        f"| OPF | {'yes' if report.has_opf else 'no'} |",
        f"| nav | {'yes' if report.has_nav else 'no'} |",
        f"| CSS | {'yes' if report.has_css else 'no'} |",
        f"| chapters | {report.chapter_count} |",
        f"| cover page | {'yes' if report.has_cover_page else 'no'} |",
        f"| cover image | {'yes' if report.has_cover_image else 'no'} |",
        "",
        "## Issues",
        "",
    ]
    if report.issues:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {safe_cell(issue.code)} | `{safe_cell(issue.path)}` | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No EPUB audit issues found.")
    return "\n".join(lines)
