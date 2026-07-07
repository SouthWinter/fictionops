from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .markdown import safe_cell
from .models import PublishMetadataIssue, PublishMetadataReport
from .plan_chapter import normalize_book_for_plan


FIELD_ALIASES = {
    "书名": "title",
    "title": "title",
    "卷名": "volume_title",
    "volume": "volume_title",
    "本名": "book_title",
    "book title": "book_title",
    "版本": "version",
    "version": "version",
    "发布日期": "release_date",
    "release date": "release_date",
    "字数": "word_count",
    "word count": "word_count",
    "作者名": "author",
    "作者": "author",
    "author": "author",
    "分类": "category",
    "category": "category",
    "标签": "tags",
    "tags": "tags",
    "简介短版": "short_synopsis",
    "短简介": "short_synopsis",
    "short synopsis": "short_synopsis",
    "简介长版": "long_synopsis",
    "长简介": "long_synopsis",
    "long synopsis": "long_synopsis",
    "关键词": "keywords",
    "keywords": "keywords",
    "封面": "cover_image",
    "封面图片": "cover_image",
    "cover": "cover_image",
    "cover image": "cover_image",
    "cover file": "cover_image",
    "是否需要内容提示": "content_warning",
    "内容提示": "content_warning",
    "content warning": "content_warning",
}

FIELD_LABELS = {
    "title": "书名",
    "volume_title": "卷名",
    "book_title": "本名",
    "version": "版本",
    "release_date": "发布日期",
    "word_count": "字数",
    "author": "作者名",
    "category": "分类",
    "tags": "标签",
    "short_synopsis": "简介短版",
    "long_synopsis": "简介长版",
    "keywords": "关键词",
    "cover_image": "封面图片",
    "content_warning": "内容提示",
}

LIST_FIELDS = {"tags", "keywords"}
REQUIRED_FIELDS = ["title", "author", "category", "tags", "short_synopsis", "long_synopsis"]
PLACEHOLDER_VALUES = {"", "-", "—", "……", "...", "待定", "未定", "暂无", "无", "TODO", "todo"}


def default_publish_checklist_path(project: Path) -> Path:
    return project / "08_publish" / "publish_checklist.md"


def default_metadata_output_path(project: Path, *, book: str) -> Path:
    return project / "08_publish" / "metadata" / f"{book}_metadata.json"


def resolve_publish_checklist_path(target: Path, *, file_path: str | None) -> Path:
    if target.is_file():
        return target.resolve()
    if file_path:
        path = Path(file_path).expanduser()
        if path.is_absolute():
            return path.resolve()
        return (target / path).resolve()
    return default_publish_checklist_path(target).resolve()


def resolve_metadata_output_path(target: Path, out_path: str | None, *, book: str) -> Path:
    resolved = target.resolve()
    if resolved.is_dir():
        base = resolved
    elif resolved.parent.name == "08_publish":
        base = resolved.parent.parent
    else:
        base = resolved.parent
    if out_path:
        output = Path(out_path).expanduser()
        if output.is_absolute():
            return output.resolve()
        return (base / output).resolve()
    return default_metadata_output_path(base, book=book).resolve()


def normalize_field_label(label: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", label.strip()).lower()
    return FIELD_ALIASES.get(cleaned)


def split_list_value(value: str) -> list[str]:
    parts = re.split(r"[、，,;；\n]+", value)
    return [part.strip() for part in parts if part.strip() and part.strip() not in PLACEHOLDER_VALUES]


def blank_value(value: object) -> bool:
    if isinstance(value, list):
        return len(value) == 0
    return str(value).strip() in PLACEHOLDER_VALUES


def blank_content_warning(value: object) -> bool:
    text = str(value).strip()
    return text in {"", "-", "—", "……", "...", "待定", "未定", "暂无", "TODO", "todo"}


def nonspace_len(value: object) -> int:
    if isinstance(value, list):
        value = " ".join(value)
    return sum(1 for char in str(value) if not char.isspace())


def empty_metadata() -> dict[str, object]:
    metadata: dict[str, object] = {}
    for key in FIELD_LABELS:
        metadata[key] = [] if key in LIST_FIELDS else ""
    return metadata


def parse_publish_metadata(text: str) -> dict[str, object]:
    raw_fields: dict[str, str] = {}
    current_key: str | None = None
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]\s*([^：:]+)[：:]\s*(.*?)\s*$", line)
        if match:
            key = normalize_field_label(match.group(1))
            current_key = key
            if key:
                raw_fields[key] = match.group(2).strip()
            continue
        stripped = line.strip()
        if current_key and stripped and not stripped.startswith(("#", "|")):
            raw_fields[current_key] = (raw_fields.get(current_key, "") + "\n" + stripped).strip()

    metadata = empty_metadata()
    for key, value in raw_fields.items():
        metadata[key] = split_list_value(value) if key in LIST_FIELDS else value.strip()
    return metadata


def metadata_issues(*, checklist_exists: bool, metadata: dict[str, object]) -> list[PublishMetadataIssue]:
    issues: list[PublishMetadataIssue] = []
    if not checklist_exists:
        issues.append(
            PublishMetadataIssue(
                severity="P2",
                code="missing_publish_checklist",
                field="-",
                message="Publish checklist was not found.",
            )
        )
        return issues

    for field in REQUIRED_FIELDS:
        if blank_value(metadata.get(field, "")):
            issues.append(
                PublishMetadataIssue(
                    severity="P2",
                    code="missing_required_metadata",
                    field=field,
                    message=f"Required publish metadata is empty: {FIELD_LABELS[field]}.",
                )
            )

    tags = metadata.get("tags", [])
    if isinstance(tags, list) and 0 < len(tags) < 2:
        issues.append(
            PublishMetadataIssue(
                severity="P3",
                code="too_few_tags",
                field="tags",
                message="Publish metadata has fewer than two tags.",
            )
        )
    if not blank_value(metadata.get("short_synopsis", "")) and nonspace_len(metadata["short_synopsis"]) < 12:
        issues.append(
            PublishMetadataIssue(
                severity="P3",
                code="short_synopsis_too_short",
                field="short_synopsis",
                message="Short synopsis is very brief; confirm it is intentional.",
            )
        )
    if not blank_value(metadata.get("long_synopsis", "")) and nonspace_len(metadata["long_synopsis"]) < 30:
        issues.append(
            PublishMetadataIssue(
                severity="P3",
                code="long_synopsis_too_short",
                field="long_synopsis",
                message="Long synopsis is very brief; confirm it is intentional.",
            )
        )
    if blank_content_warning(metadata.get("content_warning", "")):
        issues.append(
            PublishMetadataIssue(
                severity="P3",
                code="content_warning_unspecified",
                field="content_warning",
                message="Content-warning decision is not recorded.",
            )
        )
    return issues


def export_publish_metadata(
    target: Path,
    *,
    book: str,
    file_path: str | None,
    out: str | None,
    force: bool,
    dry_run: bool,
) -> PublishMetadataReport:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")

    book_id = normalize_book_for_plan(book)
    checklist = resolve_publish_checklist_path(resolved, file_path=file_path)
    output_path = resolve_metadata_output_path(resolved, out, book=book_id)
    checklist_exists = checklist.exists() and checklist.is_file()
    metadata = empty_metadata()
    if checklist_exists:
        metadata = parse_publish_metadata(checklist.read_text(encoding="utf-8"))
    elif checklist.exists() and not checklist.is_file():
        raise IsADirectoryError(f"publish checklist path is not a file: {checklist}")

    issues = metadata_issues(checklist_exists=checklist_exists, metadata=metadata)
    written = False
    if checklist_exists and not dry_run:
        if output_path.exists() and not force:
            raise FileExistsError(f"output file exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "book": book_id,
            "source": str(checklist),
            "metadata": metadata,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written = True

    return PublishMetadataReport(
        target=str(resolved),
        book=book_id,
        checklist_file=str(checklist),
        checklist_file_exists=checklist_exists,
        output_file=str(output_path),
        dry_run=dry_run,
        written=written,
        metadata=metadata,
        issues=issues,
    )


def render_publish_metadata_report(report: PublishMetadataReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported export-metadata format: {format_}")

    lines = [
        "# FictionOps Publish Metadata",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Checklist: `{report.checklist_file}`",
        f"- Checklist exists: {'yes' if report.checklist_file_exists else 'no'}",
        f"- Output: `{report.output_file or '-'}`",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        "",
        "## Metadata",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, label in FIELD_LABELS.items():
        value = report.metadata.get(key, "")
        rendered = "、".join(value) if isinstance(value, list) else str(value)
        lines.append(f"| {label} | {safe_cell(rendered)} |")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Field | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {safe_cell(issue.code)} | {safe_cell(issue.field)} | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No publish metadata issues found.")
    return "\n".join(lines)
