from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .book_gate import book_issue_blocks, build_book_gate
from .epub_audit import build_epub_audit_report
from .markdown import safe_cell
from .models import ReleaseGateCheck, ReleaseGateIssue, ReleaseGateReport
from .plan_chapter import normalize_book_for_plan
from .publish_audit import build_publish_audit_report
from .publish_manifest import default_manifest_output_path, export_publish_manifest
from .publish_metadata import export_publish_metadata


BLOCKING_SEVERITIES = {"P0", "P1", "P2"}

RELEASE_BLOCKING_CODES = {
    "missing_clean_markdown",
    "empty_clean_markdown",
    "draft_marker_left",
    "no_chapter_headings",
    "missing_publish_checklist",
    "missing_required_metadata",
    "metadata_not_exported",
    "stale_metadata",
    "missing_metadata_json",
    "invalid_metadata_json",
    "missing_cover_image",
    "manifest_not_exported",
    "stale_manifest",
    "missing_manifest",
    "missing_epub",
    "stale_epub",
    "invalid_epub_archive",
    "mimetype_not_first",
    "invalid_mimetype",
    "missing_container",
    "missing_opf",
    "missing_nav",
    "missing_css",
    "missing_chapters",
    "broken_cover_manifest",
    "cover_not_packaged",
}

ARTIFACT_CODES = {
    "missing_clean_markdown",
    "missing_publish_checklist",
    "metadata_not_exported",
    "missing_metadata_json",
    "manifest_not_exported",
    "missing_manifest",
    "missing_epub",
}

PUBLISH_SOURCES = {
    "audit-publish",
    "export-metadata",
    "export-manifest",
    "audit-epub",
}


def resolve_release_gate_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_release_gate(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def severity_blocks(severity: str) -> bool:
    return (severity or "P4").upper() in BLOCKING_SEVERITIES


def release_issue_blocks(issue: ReleaseGateIssue) -> bool:
    return severity_blocks(issue.severity) or issue.code in RELEASE_BLOCKING_CODES


def gate_issue(
    *,
    source: str,
    issue: object,
    default_subject: str = "-",
    default_path: str = "-",
) -> ReleaseGateIssue:
    return ReleaseGateIssue(
        severity=str(getattr(issue, "severity", "P4") or "P4"),
        source=source,
        code=str(getattr(issue, "code", "issue") or "issue"),
        subject=str(
            getattr(issue, "chapter", "")
            or getattr(issue, "field", "")
            or getattr(issue, "kind", "")
            or default_subject
        ),
        path=str(getattr(issue, "path", "") or default_path),
        message=str(getattr(issue, "message", "")),
    )


def book_gate_issues(book_gate) -> list[ReleaseGateIssue]:
    issues: list[ReleaseGateIssue] = []
    for issue in book_gate.issues:
        if issue.source in PUBLISH_SOURCES:
            continue
        severity = issue.severity
        if book_issue_blocks(issue) and not severity_blocks(severity):
            severity = "P2"
        issues.append(
            ReleaseGateIssue(
                severity=severity,
                source=f"book-gate:{issue.source}",
                code=issue.code,
                subject=issue.subject,
                path=issue.path,
                message=issue.message,
            )
        )
    return issues


def output_older_than(output_file: Path, input_files: list[Path]) -> bool:
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


def manifest_hashes_match(path: Path, current_manifest: dict[str, object]) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(existing, dict):
        return False
    existing_files = existing.get("files", {})
    current_files = current_manifest.get("files", {})
    if not isinstance(existing_files, dict) or not isinstance(current_files, dict):
        return False
    for key, current_file in current_files.items():
        if not isinstance(current_file, dict):
            return False
        if not current_file.get("exists", False):
            continue
        existing_file = existing_files.get(key, {})
        if not isinstance(existing_file, dict):
            return False
        if existing_file.get("sha256") != current_file.get("sha256"):
            return False
    return True


def metadata_output_issues(metadata_report, *, project: Path) -> list[ReleaseGateIssue]:
    issues: list[ReleaseGateIssue] = []
    output_path = Path(metadata_report.output_file or "")
    checklist_path = Path(metadata_report.checklist_file)
    if metadata_report.checklist_file_exists and not output_path.exists():
        issues.append(
            ReleaseGateIssue(
                severity="P2",
                source="export-metadata",
                code="metadata_not_exported",
                subject="-",
                path=str(output_path),
                message="Publish metadata JSON has not been exported yet.",
            )
        )
    elif output_path.exists() and output_older_than(output_path, [checklist_path]):
        issues.append(
            ReleaseGateIssue(
                severity="P3",
                source="export-metadata",
                code="stale_metadata",
                subject="-",
                path=str(output_path),
                message="Publish metadata JSON is older than the publish checklist.",
            )
        )
    return issues


def manifest_output_issues(manifest_report, *, project: Path) -> list[ReleaseGateIssue]:
    issues: list[ReleaseGateIssue] = []
    output_path = default_manifest_output_path(project, book=manifest_report.book)
    clean_exists = Path(manifest_report.clean_file).exists()
    metadata_exists = Path(manifest_report.metadata_file).exists()
    if clean_exists and metadata_exists and not output_path.exists():
        issues.append(
            ReleaseGateIssue(
                severity="P2",
                source="export-manifest",
                code="manifest_not_exported",
                subject="-",
                path=str(output_path),
                message="Publish manifest has not been exported yet.",
            )
        )
    elif output_path.exists() and clean_exists and metadata_exists and not manifest_hashes_match(output_path, manifest_report.manifest):
        issues.append(
            ReleaseGateIssue(
                severity="P2",
                source="export-manifest",
                code="stale_manifest",
                subject="-",
                path=str(output_path),
                message="Publish manifest hashes do not match the current publish inputs.",
            )
        )
    return issues


def check_from_issues(name: str, command: str, issues: list[ReleaseGateIssue], summary: str) -> ReleaseGateCheck:
    blocking = sum(1 for item in issues if release_issue_blocks(item))
    status = "pass" if not issues else ("blocked" if blocking else "notes")
    return ReleaseGateCheck(
        name=name,
        source_command=command,
        status=status,
        issue_count=len(issues),
        blocking_issue_count=blocking,
        summary=summary,
    )


def next_actions(status: str, issues: list[ReleaseGateIssue], *, book: str) -> list[str]:
    if status == "needs_release_artifacts":
        return [
            f"Run the publish chain for `{book}`: export-clean, export-metadata, export-manifest, export-epub.",
            f"Then rerun `fictionops release-gate . --book {book}`.",
        ]
    blocking = [item for item in issues if release_issue_blocks(item)]
    if blocking:
        sources = sorted({item.source for item in blocking})
        return [
            "Resolve release blockers from: " + ", ".join(sources) + ".",
            f"Regenerate affected artifacts, then rerun `fictionops release-gate . --book {book}`.",
        ]
    if issues:
        return [
            "Review non-blocking release notes before uploading.",
            f"Archive the release package after confirming notes are intentional.",
        ]
    return [
        "Release package is ready for upload or archive.",
        f"Keep `08_publish/manifest/{book}_manifest.json` with the uploaded artifact for reproducibility.",
    ]


def build_release_gate(
    project: Path,
    *,
    book: str = "book_01",
    min_chapter_chars: int = 200,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> ReleaseGateReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"release-gate requires a FictionOps project directory: {project}")

    resolved = project.expanduser().resolve()
    book_id = normalize_book_for_plan(book)

    book_gate = build_book_gate(
        resolved,
        book=book_id,
        outline=None,
        min_chapter_chars=min_chapter_chars,
        out=None,
        force=False,
        dry_run=True,
    )

    publish = build_publish_audit_report(
        resolved,
        book=book_id,
        file_path=None,
        min_chapter_chars=min_chapter_chars,
    )
    metadata = export_publish_metadata(
        resolved,
        book=book_id,
        file_path=None,
        out=None,
        force=False,
        dry_run=True,
    )
    manifest = export_publish_manifest(
        resolved,
        book=book_id,
        clean_file=None,
        metadata_file=None,
        out=None,
        force=False,
        dry_run=True,
    )
    epub = build_epub_audit_report(
        resolved,
        book=book_id,
        file_path=None,
        manifest_file=None,
        clean_file=None,
        metadata_file=None,
    )

    publish_issues = [gate_issue(source="audit-publish", issue=item) for item in publish.issues]
    metadata_issues = [gate_issue(source="export-metadata", issue=item, default_path=metadata.checklist_file) for item in metadata.issues]
    metadata_issues.extend(metadata_output_issues(metadata, project=resolved))
    manifest_issues = [gate_issue(source="export-manifest", issue=item) for item in manifest.issues]
    manifest_issues.extend(manifest_output_issues(manifest, project=resolved))
    epub_issues = [gate_issue(source="audit-epub", issue=item) for item in epub.issues]
    closure_issues = book_gate_issues(book_gate)
    issues = closure_issues + publish_issues + metadata_issues + manifest_issues + epub_issues

    checks = [
        check_from_issues(
            "Book closure",
            "book-gate",
            closure_issues,
            f"status={book_gate.status}, ready={book_gate.ready}, issues={book_gate.issue_count}.",
        ),
        check_from_issues(
            "Clean Markdown",
            "audit-publish",
            publish_issues,
            f"exists={publish.clean_file_exists}, chapters={publish.clean_chapters}, drafts={publish.draft_chapters}.",
        ),
        check_from_issues(
            "Publish metadata",
            "export-metadata",
            metadata_issues,
            f"checklist={metadata.checklist_file_exists}, output={bool(metadata.output_file and Path(metadata.output_file).exists())}.",
        ),
        check_from_issues(
            "Publish manifest",
            "export-manifest",
            manifest_issues,
            f"output={Path(manifest.output_file).exists()}, files={len(manifest.files)}.",
        ),
        check_from_issues(
            "EPUB package",
            "audit-epub",
            epub_issues,
            f"exists={epub.epub_file_exists}, valid={epub.epub_valid}, chapters={epub.chapter_count}.",
        ),
    ]

    blocking_count = sum(1 for item in issues if release_issue_blocks(item))
    blocking_codes = {item.code for item in issues if release_issue_blocks(item)}
    if blocking_codes & ARTIFACT_CODES:
        status = "needs_release_artifacts"
        ready = False
    elif blocking_count:
        status = "needs_release_fixes"
        ready = False
    elif issues:
        status = "release_notes"
        ready = True
    else:
        status = "ready_for_release"
        ready = True

    output_path = resolve_release_gate_output_path(resolved, out) if out else None
    report = ReleaseGateReport(
        target=str(resolved),
        book=book_id,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        status=status,
        ready=ready,
        issue_count=len(issues),
        blocking_issue_count=blocking_count,
        checks=checks,
        issues=issues,
        next_actions=next_actions(status, issues, book=book_id),
        book_gate=book_gate,
        publish=publish,
        metadata=metadata,
        manifest=manifest,
        epub=epub,
    )
    if output_path and not dry_run:
        write_release_gate(output_path, render_release_gate(report, "markdown"), force=force)
        report.written = True
    return report


def render_release_gate(report: ReleaseGateReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_release_gate(report)


def format_release_gate(report: ReleaseGateReport) -> str:
    lines = [
        "# FictionOps Release Gate",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Issues: {report.issue_count}",
        f"- Blocking issues: {report.blocking_issue_count}",
        "",
        "## Checks",
        "",
        "| Check | Status | Issues | Blocking | Source | Summary |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            "| "
            + " | ".join(
                [
                    safe_cell(check.name),
                    safe_cell(check.status),
                    str(check.issue_count),
                    str(check.blocking_issue_count),
                    f"`{safe_cell(check.source_command)}`",
                    safe_cell(check.summary),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Source | Code | Subject | Path | Message |", "| --- | --- | --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(item.severity),
                        safe_cell(item.source),
                        f"`{safe_cell(item.code)}`",
                        safe_cell(item.subject),
                        f"`{safe_cell(item.path)}`",
                        safe_cell(item.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No release-gate issues found.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
