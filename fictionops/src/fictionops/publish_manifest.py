from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .export_clean import default_clean_output_path
from .markdown import is_cjk, safe_cell
from .models import PublishManifestFile, PublishManifestIssue, PublishManifestReport
from .plan_chapter import normalize_book_for_plan
from .publish_metadata import blank_value, default_metadata_output_path


MANIFEST_SCHEMA = "fictionops.publish_manifest.v1"


def default_manifest_output_path(project: Path, *, book: str) -> Path:
    return project / "08_publish" / "manifest" / f"{book}_manifest.json"


def resolve_manifest_file(project: Path, file_path: str | None, *, default_path: Path) -> Path:
    if not file_path:
        return default_path.resolve()
    path = Path(file_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project / path).resolve()


def file_manifest(kind: str, path: Path, *, project: Path) -> PublishManifestFile:
    if not path.exists():
        return PublishManifestFile(
            kind=kind,
            path=str(path),
            exists=False,
            bytes=0,
            sha256="",
            chars=0,
            nonspace_chars=0,
            cjk_chars=0,
            lines=0,
        )
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = ""
    return PublishManifestFile(
        kind=kind,
        path=str(path),
        exists=True,
        bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        chars=len(text),
        nonspace_chars=sum(1 for char in text if not char.isspace()),
        cjk_chars=sum(1 for char in text if is_cjk(char)),
        lines=text.count("\n") + (1 if text and not text.endswith("\n") else 0),
    )


def manifest_issue_for_missing(kind: str, path: Path) -> PublishManifestIssue:
    return PublishManifestIssue(
        severity="P2",
        code=f"missing_{kind}",
        path=str(path),
        message=f"Required publish package file was not found: {path}",
    )


def load_metadata_payload(path: Path, issues: list[PublishManifestIssue]) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            PublishManifestIssue(
                severity="P2",
                code="invalid_metadata_json",
                path=str(path),
                message=f"Metadata JSON could not be parsed: {exc}",
            )
        )
        return {}
    if not isinstance(payload, dict):
        issues.append(
            PublishManifestIssue(
                severity="P2",
                code="invalid_metadata_json",
                path=str(path),
                message="Metadata JSON root must be an object.",
            )
        )
        return {}
    return payload


def resolve_metadata_cover_path(project: Path, metadata: dict[str, object]) -> Path | None:
    cover_value = metadata.get("cover_image", "")
    if blank_value(cover_value):
        return None
    cover_text = str(cover_value).strip()
    if not cover_text:
        return None
    return resolve_manifest_file(project, cover_text, default_path=Path(cover_text))


def build_manifest_payload(
    *,
    book: str,
    clean_file: PublishManifestFile,
    metadata_file: PublishManifestFile,
    cover_file: PublishManifestFile | None,
    metadata_payload: dict[str, object],
) -> dict[str, object]:
    metadata = metadata_payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    files = {
        "clean_markdown": asdict(clean_file),
        "metadata_json": asdict(metadata_file),
    }
    if cover_file is not None:
        files["cover_image"] = asdict(cover_file)
    return {
        "schema": MANIFEST_SCHEMA,
        "book": book,
        "files": files,
        "metadata": metadata,
        "sources": {
            "metadata_source": metadata_payload.get("source", ""),
        },
    }


def export_publish_manifest(
    project: Path,
    *,
    book: str,
    clean_file: str | None,
    metadata_file: str | None,
    out: str | None,
    force: bool,
    dry_run: bool,
) -> PublishManifestReport:
    resolved = project.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"path is not a directory: {resolved}")

    book_id = normalize_book_for_plan(book)
    clean_path = resolve_manifest_file(
        resolved,
        clean_file,
        default_path=default_clean_output_path(resolved, book=book_id),
    )
    metadata_path = resolve_manifest_file(
        resolved,
        metadata_file,
        default_path=default_metadata_output_path(resolved, book=book_id),
    )
    output_path = resolve_manifest_file(
        resolved,
        out,
        default_path=default_manifest_output_path(resolved, book=book_id),
    )

    issues: list[PublishManifestIssue] = []
    clean_manifest = file_manifest("clean_markdown", clean_path, project=resolved)
    metadata_manifest = file_manifest("metadata_json", metadata_path, project=resolved)
    if not clean_manifest.exists:
        issues.append(manifest_issue_for_missing("clean_markdown", clean_path))
    if not metadata_manifest.exists:
        issues.append(manifest_issue_for_missing("metadata_json", metadata_path))
    metadata_payload = load_metadata_payload(metadata_path, issues)
    metadata = metadata_payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    cover_path = resolve_metadata_cover_path(resolved, metadata)
    cover_manifest = file_manifest("cover_image", cover_path, project=resolved) if cover_path else None
    if cover_manifest is not None and not cover_manifest.exists:
        issues.append(manifest_issue_for_missing("cover_image", cover_path))
    manifest = build_manifest_payload(
        book=book_id,
        clean_file=clean_manifest,
        metadata_file=metadata_manifest,
        cover_file=cover_manifest,
        metadata_payload=metadata_payload,
    )

    written = False
    if not dry_run:
        if output_path.exists() and not force:
            raise FileExistsError(f"output file exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written = True

    return PublishManifestReport(
        target=str(resolved),
        book=book_id,
        output_file=str(output_path),
        dry_run=dry_run,
        written=written,
        clean_file=str(clean_path),
        metadata_file=str(metadata_path),
        manifest=manifest,
        files=[clean_manifest, metadata_manifest],
        issues=issues,
    )


def render_publish_manifest_report(report: PublishManifestReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported export-manifest format: {format_}")

    lines = [
        "# FictionOps Publish Manifest",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Output: `{report.output_file}`",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        "",
        "| Kind | Exists | Bytes | SHA256 | Path |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for file in report.files:
        sha = file.sha256[:12] if file.sha256 else "-"
        lines.append(
            f"| {safe_cell(file.kind)} | {'yes' if file.exists else 'no'} | {file.bytes} | "
            f"{sha} | `{safe_cell(file.path)}` |"
        )

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {safe_cell(issue.code)} | `{safe_cell(issue.path)}` | "
                f"{safe_cell(issue.message)} |"
            )
    else:
        lines.append("No publish manifest issues found.")
    return "\n".join(lines)
